set dcp E:/new/fpga_lock/v94/v0.94/exp/l1-contract-20260909/current_routed.dcp
open_checkpoint $dcp
puts "CLOCKS=[get_clocks]"
puts "DNA_CELLS=[get_cells -hierarchical -filter {REF_NAME == FD* && NAME =~ *dna*}]"
puts "DNA_PINS=[get_pins -hierarchical -filter {NAME =~ *i_DNA*/* || NAME =~ *dna_clk*}]"
puts "HK_CELLS=[get_cells -hierarchical -filter {NAME =~ *i_hk*}]"
puts "PORTS_DAISY=[get_ports {daisy_*}]"
report_clocks -file E:/new/fpga_lock/v94/v0.94/exp/l1-candidate-20260911/query_clocks.rpt
close_design
exit
