// Module slice: N data lanes plus one forwarded-clock lane per direction,
// digital half only (spec sections 1, 4, 5). Quarter-rate: 4 bits per lane
// per parallel-clock cycle. The drawn cells (TX last 2:1 stage and driver, RX
// input stage and sampler) sit on the boundary ports listed in rtl/README.md.
// No rate or timing claim is made here; that is a post-route STA statement.
module slice #(
    parameter N = 16
) (
    input  wire             clk,         // parallel clock (supplied, out of scope)
    input  wire             rst_n,       // clk-domain reset, deassert synchronous to clk
    input  wire             rx_rst_n,    // rx_clk-domain reset, deassert synchronous to rx_clk

    // core side, TX: valid/ready per slice
    input  wire             link_ready,  // link/training state, out of scope
    input  wire             tx_valid,
    output reg              tx_ready,
    input  wire [4*N-1:0]   tx_data,

    // core side, RX: valid only, no back-pressure
    output wire             rx_valid,
    output wire [4*N-1:0]   rx_data,
    output wire             rx_overflow, // sticky, rx_clk domain; status only

    // drawn-cell boundary, TX
    output wire [2*N-1:0]   tx_a,
    output wire [2*N-1:0]   tx_b,
    output wire             tx_fwd_en,   // forwarded-clock lane: gate open for this word

    // drawn-cell boundary, RX
    input  wire             rx_clk,      // forwarded clock at parallel rate, toggles only per word
    input  wire [2*N-1:0]   rx_a,
    input  wire [2*N-1:0]   rx_b
);
    wire accept = tx_valid & tx_ready;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) tx_ready <= 1'b0;
        else        tx_ready <= link_ready;
    end

    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : g_lane
            lane_tx_ser u_tx (
                .clk  (clk),
                .rst_n(rst_n),
                .load (accept),
                .din  (tx_data[4*i +: 4]),
                .tx_a (tx_a[2*i +: 2]),
                .tx_b (tx_b[2*i +: 2])
            );
        end
    endgenerate

    // forwarded-clock lane, TX: gate open exactly for cycles that carry a word
    reg fwd_en_q;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) fwd_en_q <= 1'b0;
        else        fwd_en_q <= accept;
    end
    assign tx_fwd_en = fwd_en_q;

    wire [4*N-1:0] des_word;
    generate
        for (i = 0; i < N; i = i + 1) begin : g_rlane
            lane_rx_des u_rx (
                .rx_a(rx_a[2*i +: 2]),
                .rx_b(rx_b[2*i +: 2]),
                .dout(des_word[4*i +: 4])
            );
        end
    endgenerate

    rx_cdc_fifo #(.W(4*N)) u_cdc (
        .wclk    (rx_clk),
        .wrst_n  (rx_rst_n),
        .wdata   (des_word),
        .overflow(rx_overflow),
        .rclk    (clk),
        .rrst_n  (rst_n),
        .rdata   (rx_data),
        .rvalid  (rx_valid)
    );
endmodule
