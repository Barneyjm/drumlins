cd /home/claude && python3 fetch_pl.py stg 14.75 53.15 15.55 53.55 > stg/fetch.log 2>&1
python3 fetch_pl.py zbo 18.85 52.80 19.55 53.20 > zbo/fetch.log 2>&1
for f in stg zbo; do cd /home/claude/$f && python3 run_ny.py > run_ny.log 2>&1 && PRE_CLOSE=3 SUF=_closed3 python3 candidates.py > cand.log 2>&1 && python3 /home/claude/score_field.py /home/claude/$f > score.log 2>&1 && python3 check_sheets.py > chk.log 2>&1; echo "$f done $?" >> /home/claude/fields_pl.log; done
