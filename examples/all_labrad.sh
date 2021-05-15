set -x
set -e

EXAMPLES="./"

(cd ${EXAMPLES}/setup_verify_labrad/; python setup_verify_labrad.py)
(cd ${EXAMPLES}/bram_accum_send_recv_labrad/; python bram_accum_send_recv_labrad.py)
(cd ${EXAMPLES}/bram_send_recv_labrad/; python bram_send_recv_labrad.py)
(cd ${EXAMPLES}/dram_iq_send_recv_labrad/; python dram_iq_send_recv_labrad.py)
(cd ${EXAMPLES}/dram_send_2ch_250ms_labrad/; python dram_send_2ch_250ms_labrad.py)
(cd ${EXAMPLES}/dram_send_recv_2ch_250ms_labrad/; python dram_send_recv_2ch_250ms_labrad.py)
(cd ${EXAMPLES}/feedback_test_1_labrad/; python feedback_test_1_labrad.py)
(cd ${EXAMPLES}/feedback_test_2_labrad/; python feedback_test_2_labrad.py)
(cd ${EXAMPLES}/rftool_labrad_server/; python rftool_labrad_server.py)
