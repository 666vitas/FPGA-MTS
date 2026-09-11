set project_file {E:/new/fpga_lock/v94/v0.94/project/redpitaya.xpr}
set run_name {l1_candidate_impl_final_20260911}
set release_dir {E:/new/fpga_lock/releases/20260911_LOCK-MVP-L1_CANDIDATE_8fc084e}
set bit_file [file join $release_dir red_pitaya_top_CANDIDATE.bit]

if {![file exists $project_file]} { error "missing project: $project_file" }
file mkdir $release_dir
open_project $project_file
set run [get_runs $run_name]
if {[llength $run] != 1} { error "required implementation run not found: $run_name" }
set run_status [get_property STATUS $run]
if {$run_status ne {route_design Complete!}} {
  error "refusing bitstream: $run_name status is '$run_status'"
}
open_run $run_name
set design_state {Fully Routed}
set timing [report_timing_summary -return_string -delay_type min_max -check_timing_verbose]
if {![regexp {All user specified timing constraints are met} $timing]} {
  error "refusing bitstream: timing summary did not report all user constraints met"
}
set drc [report_drc -return_string]
if {[regexp -nocase {Critical Warning|Error} $drc]} {
  error "refusing bitstream: DRC contains Critical Warning or Error"
}
write_bitstream -force $bit_file
set fp [open [file join $release_dir bit_generation_identity.txt] w]
puts $fp "Vivado=2020.1"
puts $fp "XPR=$project_file"
puts $fp "Run=$run_name"
puts $fp "RunStatus=$run_status"
puts $fp "DesignState=$design_state"
puts $fp "Bit=$bit_file"
puts $fp "HEAD=8fc084e55cc353813edc980559a8f78fdec4658c"
close $fp
close_project
exit
