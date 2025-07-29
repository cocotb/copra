// Copyright copra contributors
// Licensed under the Revised BSD License, see LICENSE for details.
// SPDX-License-Identifier: BSD-3-Clause

module multi_dim_array (

  //INPUTS

  //Single dimensions
  input     logic               [2:0]               in_vect_packed,
  input     logic                                   in_vect_unpacked[2:0],
  input     logic               [2:0]               in_arr,

  //2 dimensions
  input     logic               [2:0][2:0]          in_2d_vect_packed_packed,
  input     logic               [2:0]               in_2d_vect_packed_unpacked[2:0],
  input     logic                                   in_2d_vect_unpacked_unpacked[2:0][2:0],

  input     logic               [2:0][2:0]          in_arr_packed,
  input     logic               [2:0]               in_arr_unpacked[2:0],
  input     logic               [2:0][2:0]          in_2d_arr,

  //3 dimensions
  input     logic               [2:0][2:0][2:0]     in_vect_packed_packed_packed,
  input     logic               [2:0][2:0]          in_vect_packed_packed_unpacked[2:0],
  input     logic               [2:0]               in_vect_packed_unpacked_unpacked[2:0][2:0],
  input     logic                                   in_vect_unpacked_unpacked_unpacked[2:0][2:0][2:0],

  input     logic               [2:0][2:0][2:0]     in_arr_packed_packed,
  input     logic               [2:0][2:0]          in_arr_packed_unpacked[2:0],
  input     logic               [2:0]               in_arr_unpacked_unpacked[2:0][2:0],

  input     logic               [2:0][2:0][2:0]     in_2d_arr_packed,
  input     logic               [2:0][2:0]          in_2d_arr_unpacked[2:0],

  input     logic               [2:0][2:0][2:0]     in_3d_arr,


  //OUTPUTS
  //Single dimensions
  output    logic               [2:0]               out_vect_packed,
  output    logic                                   out_vect_unpacked[2:0],
  output    logic               [2:0]               out_arr,

  //2 dimensions
  output    logic               [2:0][2:0]          out_2d_vect_packed_packed,
  output    logic               [2:0]               out_2d_vect_packed_unpacked[2:0],
  output    logic                                   out_2d_vect_unpacked_unpacked[2:0][2:0],

  output    logic               [2:0][2:0]          out_arr_packed,
  output    logic               [2:0]               out_arr_unpacked[2:0],
  output    logic               [2:0][2:0]          out_2d_arr,

  //3 dimensions
  output    logic               [2:0][2:0][2:0]     out_vect_packed_packed_packed,
  output    logic               [2:0][2:0]          out_vect_packed_packed_unpacked[2:0],
  output    logic               [2:0]               out_vect_packed_unpacked_unpacked[2:0][2:0],
  output    logic                                   out_vect_unpacked_unpacked_unpacked[2:0][2:0][2:0],

  output    logic               [2:0][2:0][2:0]     out_arr_packed_packed,
  output    logic               [2:0][2:0]          out_arr_packed_unpacked[2:0],
  output    logic               [2:0]               out_arr_unpacked_unpacked[2:0][2:0],

  output    logic               [2:0][2:0][2:0]     out_2d_arr_packed,
  output    logic               [2:0][2:0]          out_2d_arr_unpacked[2:0],

  output    logic               [2:0][2:0][2:0]     out_3d_arr

);

//Fairly simple passthrough of all the values...

assign out_vect_packed                              = in_vect_packed;
assign out_vect_unpacked                            = in_vect_unpacked;
assign out_arr                                      = in_arr;

assign out_2d_vect_packed_packed                    = in_2d_vect_packed_packed;
assign out_2d_vect_packed_unpacked                  = in_2d_vect_packed_unpacked;
assign out_2d_vect_unpacked_unpacked                = in_2d_vect_unpacked_unpacked;

assign out_arr_packed                               = in_arr_packed;
assign out_arr_unpacked                             = in_arr_unpacked;
assign out_2d_arr                                   = in_2d_arr;

assign out_vect_packed_packed_packed                = in_vect_packed_packed_packed;
assign out_vect_packed_packed_unpacked              = in_vect_packed_packed_unpacked;
assign out_vect_packed_unpacked_unpacked            = in_vect_packed_unpacked_unpacked;
assign out_vect_unpacked_unpacked_unpacked          = in_vect_unpacked_unpacked_unpacked;

assign out_arr_packed_packed                        = in_arr_packed_packed;
assign out_arr_packed_unpacked                      = in_arr_packed_unpacked;
assign out_arr_unpacked_unpacked                    = in_arr_unpacked_unpacked;

assign out_2d_arr_packed                            = in_2d_arr_packed;
assign out_2d_arr_unpacked                          = in_2d_arr_unpacked;

assign out_3d_arr                                   = in_3d_arr;

endmodule 
