// Gray-pointer asynchronous FIFO, 8 entries. Write side runs on the
// forwarded-clock domain (wclk) and writes on every wclk edge, because the
// forwarded clock only toggles while a word is on the link. Read side runs on
// the parallel clock (rclk) and presents a registered word plus valid; the
// word is meaningful only while valid is high. There is no back-pressure into
// the link: a write into a full FIFO is dropped and latches the sticky
// overflow flag (wclk domain, a status output).
module rx_cdc_fifo #(
    parameter W = 4,
    // Replicas of the registered one-hot read-select; each drives about W/COPIES
    // data bits (decision 0009 option 1). COPIES must divide W.
    parameter COPIES = 2,
    // 1 adds a read-pipeline stage between the 8:1 mux and rdata/rvalid, one rclk
    // more latency (#72 r6, decision 0009). Measured, not adopted: 0.
    parameter RPIPE = 0
) (
    input  wire           wclk,
    input  wire           wrst_n,
    input  wire [W-1:0]   wdata,
    output reg            overflow,
    input  wire           rclk,
    input  wire           rrst_n,
    output reg  [W-1:0]   rdata,
    output reg            rvalid
);
    // Optional read-pipeline stage (RPIPE = 1): rdata_p/rvalid_p hold the word one
    // rclk before rdata/rvalid. Unused, and removed by synthesis, when RPIPE = 0.
    reg [W-1:0] rdata_p;
    reg         rvalid_p;
    reg [W-1:0] mem [0:7];

    reg  [3:0] rbin, rgray;

    // write side
    reg  [3:0] wbin, wgray;
    reg  [3:0] rgray_w1, rgray_w2;
    wire [3:0] wbin_n  = wbin + 4'd1;
    wire [3:0] wgray_n = wbin_n ^ (wbin_n >> 1);
    wire       full    = (wgray_n == {~rgray_w2[3:2], rgray_w2[1:0]});

    always @(posedge wclk or negedge wrst_n) begin
        if (!wrst_n) begin
            wbin     <= 4'd0;
            wgray    <= 4'd0;
            rgray_w1 <= 4'd0;
            rgray_w2 <= 4'd0;
            overflow <= 1'b0;
        end else begin
            rgray_w1 <= rgray;
            rgray_w2 <= rgray_w1;
            if (full) begin
                overflow <= 1'b1;
            end else begin
                mem[wbin[2:0]] <= wdata;
                wbin           <= wbin_n;
                wgray          <= wgray_n;
            end
        end
    end

    // read side
    reg  [3:0] wgray_r1;

    // Registered one-hot read select, replicated. rsel[c][k] is high when
    // rbin[2:0] == k; it advances exactly when rbin does, so the mux needs no
    // 3-to-8 decode and each flop drives only W/COPIES AND terms. The keep
    // attribute stops synthesis merging the identical replicas.
    localparam G = W / COPIES;
    (* keep *) reg [7:0] rsel [0:COPIES-1];
    wire [W-1:0] rdata_n;
    genvar gc, gb, gk;
    generate
        for (gc = 0; gc < COPIES; gc = gc + 1) begin : g_sel
            for (gb = 0; gb < G; gb = gb + 1) begin : g_bit
                wire [7:0] terms;
                for (gk = 0; gk < 8; gk = gk + 1) begin : g_k
                    assign terms[gk] = rsel[gc][gk] & mem[gk][gc*G+gb];
                end
                assign rdata_n[gc*G+gb] = |terms;
            end
        end
    endgenerate

    wire [3:0] rbin_n  = rbin + 4'd1;
    wire [3:0] rgray_n = rbin_n ^ (rbin_n >> 1);
    integer ci;

    // Registered `empty` (decision 0009 follow-up, #72 r5). Equal to
    // (rgray == wgray_r2) on every cycle, where wgray_r2 is the second synchronizer
    // stage, i.e. wgray_r1 delayed one rclk; it is computed one cycle ahead from the
    // next-state pointers so the pointer increment is gated by a flop output
    // instead of a 4-bit Gray compare. wgray_r2 would take wgray_r1 on the next
    // edge, so wgray_r2 is not kept as a register; rgray takes rgray_n only if the
    // FIFO is not empty now. Both compares are
    // formed in parallel and `empty` only selects between them. No latency change.
    // rgray_nx is a registered copy of rgray_n (Gray code of rbin + 1), advanced
    // with the pointer, so the advance-case compare starts at a flop and does not
    // pass through the incrementer carry chain.
    reg        empty;
    reg  [3:0] rgray_nx;
    wire [3:0] rbin_n2   = rbin + 4'd2;
    wire [3:0] rgray_n2  = rbin_n2 ^ (rbin_n2 >> 1);
    wire       eq_hold = (rgray    == wgray_r1);
    wire       eq_adv  = (rgray_nx == wgray_r1);
    wire       empty_n = empty ? eq_hold : eq_adv;

    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rbin     <= 4'd0;
            rgray    <= 4'd0;
            wgray_r1 <= 4'd0;
            empty    <= 1'b1;
            rgray_nx <= 4'b0001;
            rdata_p  <= {W{1'b0}};
            rvalid_p <= 1'b0;
            rdata    <= {W{1'b0}};
            rvalid   <= 1'b0;
            for (ci = 0; ci < COPIES; ci = ci + 1)
                rsel[ci] <= 8'b0000_0001;
        end else begin
            wgray_r1 <= wgray;
            empty    <= empty_n;
            rvalid_p <= !empty;
            rvalid   <= RPIPE ? rvalid_p : !empty;
            // rdata loads every edge so `empty` does not fan out to the data
            // bits (decision 0007); rvalid marks the word, rdata is undefined
            // while rvalid is low.
            rdata_p  <= rdata_n;
            rdata    <= RPIPE ? rdata_p : rdata_n;
            if (!empty) begin
                rbin  <= rbin_n;
                rgray <= rgray_n;
                rgray_nx <= rgray_n2;
                for (ci = 0; ci < COPIES; ci = ci + 1)
                    rsel[ci] <= {rsel[ci][6:0], rsel[ci][7]};
            end
        end
    end
endmodule
