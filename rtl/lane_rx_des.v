// RX lane deserializer, digital half. Mirror of lane_tx_ser: reassembles the
// 4-bit word from the two 2-bit streams delivered by the drawn RX cell
// (input stage and sampler). Purely combinational: the capture register is
// the CDC FIFO entry in rx_cdc_fifo, so the last word of a burst is never
// held back waiting for another forwarded-clock edge.
module lane_rx_des (
    input  wire [1:0] rx_a,   // boundary: stream a, [0] first on the line
    input  wire [1:0] rx_b,   // boundary: stream b, [0] first on the line
    output wire [3:0] dout
);
    assign dout = {rx_b[1], rx_a[1], rx_b[0], rx_a[0]};
endmodule
