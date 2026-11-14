# Agreement analysis — step 1 (overall agreement)

- Script: `src/11_agreement_overall.py`
- Inputs: frozen `evaluation_200_labelled.xlsx` and `ai_classifications.csv`
- Items: 200 (all kept, including uncertain human annotations)
- Overall agreement: 162/200 = 0.8100

## Confusion matrix (rows = human, columns = AI; order World, Sports, Business, Sci/Tech)

```
                ai_World  ai_Sports  ai_Business  ai_Sci/Tech
human_World           51          3           14            5
human_Sports           1         50            2            0
human_Business         2          0           39           11
human_Sci/Tech         0          0            0           22
```

- Matrix total: 200; diagonal: 162 (equals agreement count).

Interpretation: this is agreement with one human reference, not accuracy
against unquestionable ground truth.
