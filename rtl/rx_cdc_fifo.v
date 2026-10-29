// Gray-pointer asynchronous FIFO, 8 entries. Write side runs on the
// forwarded-clock domain (wclk) and writes on every wclk edge, because the
// forwarded clock only toggles while a word is on the link. Read side runs on
// the parallel clock (rclk) and presents a registered word plus valid; the
// word is meaningful only while valid is high. There is no back-pressure into
// the link: a write into a full FIFO is dropped and latches the sticky
// overflow flag (wclk domain, a status output).
module rx_cdc_fifo #(
    parameter W = 4
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
    reg  [3:0] wgray_r1, wgray_r2;
    wire [3:0] rbin_n  = rbin + 4'd1;
    wire [3:0] rgray_n = rbin_n ^ (rbin_n >> 1);
    wire       empty   = (rgray == wgray_r2);

    always @(posedge rclk or negedge rrst_n) begin
        if (!rrst_n) begin
            rbin     <= 4'd0;
            rgray    <= 4'd0;
            wgray_r1 <= 4'd0;
            wgray_r2 <= 4'd0;
            rdata    <= {W{1'b0}};
            rvalid   <= 1'b0;
        end else begin
            wgray_r1 <= wgray;
            wgray_r2 <= wgray_r1;
            rvalid   <= !empty;
            // rdata loads every edge so `empty` does not fan out to the data
            // bits (decision 0007); rvalid marks the word, rdata is undefined
            // while rvalid is low.
            rdata    <= mem[rbin[2:0]];
            if (!empty) begin
                rbin  <= rbin_n;
                rgray <= rgray_n;
            end
        end
    end
endmodule
