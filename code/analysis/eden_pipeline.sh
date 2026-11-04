cd /home/claude && python3 fetch_ea.py eden -3.05 54.40 -2.25 54.95 > eden/fetch.log 2>&1
cd /home/claude/eden && python3 run_ny.py > run_ny.log 2>&1 && PRE_CLOSE=3 SUF=_closed3 python3 candidates.py > cand.log 2>&1 && python3 /home/claude/score_field.py /home/claude/eden > score.log 2>&1 && python3 check_sheets.py > chk.log 2>&1; echo "eden done $?" >> /home/claude/fields_pl.log
