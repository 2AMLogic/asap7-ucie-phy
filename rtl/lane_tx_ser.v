// TX lane serializer, digital half. Takes one 4-bit word per parallel-clock
// cycle and stops at the drawn-cell boundary: two streams of two bits each.
// Line order is d[0], d[1], d[2], d[3]; stream a carries d[0] then d[2],
// stream b carries d[1] then d[3]. The drawn TX cell does the remaining 2:1
// stages (spec section 4). No rate is implied by this module.
module lane_tx_ser (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       load,   // accept din this cycle
    input  wire [3:0] din,
    output reg  [1:0] tx_a,   // boundary: stream a, [0] first on the line
    output reg  [1:0] tx_b    // boundary: stream b, [0] first on the line
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_a <= 2'b00;
            tx_b <= 2'b00;
        end else if (load) begin
            tx_a <= {din[2], din[0]};
            tx_b <= {din[3], din[1]};
        end else begin
            tx_a <= 2'b00;
            tx_b <= 2'b00;
        end
    end
endmodule
