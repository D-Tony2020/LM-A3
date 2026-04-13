# Assignment 4

## Virtual environment creation

It's highly recommended to use a virtual environment for each assignment.
You may use environment manager like uv, conda, venv etc.
Here is how you can create an environment with uv and install dependencies.

To install uv
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

To download required dependencies using uv
```sh
cd a4/
uv sync
```

To run python programs using the new environment
```sh
uv run evaluate.py
```

## Unit tests commands

It's recommended to ensure that your completed implementation passes the unit tests before submitting it.
The commands can be run from the root directory of the project.

```sh
uv run pytest
```

This starter repository is intentionally incomplete, so some tests will fail until students implement the TODOs.

Please do NOT commit any code that changes the following files and directories:

- tests/
- .github/
- pytest.ini

Otherwise, your submission may be flagged by GitHub Classroom autograder.

## Evaluation commands

If you have saved predicted SQL queries and associated database records, you can compute F1 scores using:
```sh
uv run evaluate.py \
  --predicted_sql results/t5_ft_dev.sql \
  --predicted_records records/t5_ft_dev.pkl \
  --development_sql data/dev.sql \
  --development_records records/ground_truth_dev.pkl
```

## Submission

Please DO commit your final output files in `results/` and `records/` following the required names and formats.
Please only submit your final files corresponding to the test set.

For SQL queries, ensure that the name of the submission files (in the `results/` subfolder) are:

- `{t5_ft, ft_scr, gemma}_test.sql`

For database records, ensure that the name of the submission files (in the `records/` subfolder) are:

- `{t5_ft, ft_scr, gemma}_test.pkl`

Note that the predictions in each line of the `.sql` file or in each index of the list within the `.pkl` file must match each natural language query in `data/test.nl` in the order they appear.

For the LLM, even if you experimented with both models, you should submit only one `.sql` file and one `.pkl` file, corresponding to the model of your choice. Do not submit separate result files for each model.

The leaderboard is available here: <https://github.com/Cornell-Tech-CS5744-Spring-2026/leaderboards/>.