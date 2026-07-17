import sqlite3
import pandas as pd

DB_PATH = "teiko.db"
CSV_PATH = "cell-count.csv"

CELL_POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

# Part 1

# Data Definition Language (DDL) statements to create the database schema
DDL = """
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id  TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL REFERENCES projects(project_id),
    condition   TEXT NOT NULL,
    age         INTEGER NOT NULL,
    sex         TEXT NOT NULL,
    treatment   TEXT NOT NULL,
    response    TEXT
);

CREATE TABLE IF NOT EXISTS samples (
    sample_id                  TEXT PRIMARY KEY,
    subject_id                 TEXT NOT NULL REFERENCES subjects(subject_id),
    sample_type                TEXT NOT NULL,
    time_from_treatment_start  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cell_counts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id   TEXT NOT NULL REFERENCES samples(sample_id),
    population  TEXT NOT NULL,
    count       INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_subjects_project  ON subjects(project_id);
CREATE INDEX IF NOT EXISTS idx_samples_subject   ON samples(subject_id);
CREATE INDEX IF NOT EXISTS idx_cell_counts_sample ON cell_counts(sample_id);
CREATE INDEX IF NOT EXISTS idx_cell_counts_pop   ON cell_counts(population);
"""


def load(db_path: str = DB_PATH, csv_path: str = CSV_PATH) -> None:
    df = pd.read_csv(csv_path)

    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")

    for stmt in DDL.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            con.execute(stmt)
    con.commit()

    # projects
    projects = df[["project"]].drop_duplicates().rename(columns={"project": "project_id"})
    projects.to_sql("projects", con, if_exists="append", index=False)

    # subjects — treatment and response are constant per subject (confirmed in EDA)
    subjects = (
        df[["subject", "project", "condition", "age", "sex", "treatment", "response"]]
        .drop_duplicates("subject") #shouldn't be duplicates
        .rename(columns={"subject": "subject_id", "project": "project_id"})
    )
    subjects.to_sql("subjects", con, if_exists="append", index=False)

    # samples
    samples = (
        df[["sample", "subject", "sample_type", "time_from_treatment_start"]]
        .rename(columns={"sample": "sample_id", "subject": "subject_id"})
    )
    samples.to_sql("samples", con, if_exists="append", index=False)

    # cell_counts — melt wide → long
    cell_long = df[["sample"] + CELL_POPULATIONS].melt(
        id_vars="sample",
        var_name="population",
        value_name="count"
    ).rename(columns={"sample": "sample_id"})
    cell_long.to_sql("cell_counts", con, if_exists="append", index=False)

    con.commit()
    con.close()

    print(f"Loaded {len(df):,} rows into {db_path}")
    print(f"  projects : {projects.shape[0]}")
    print(f"  subjects : {subjects.shape[0]}")
    print(f"  samples  : {samples.shape[0]}")
    print(f"  cell_counts: {len(cell_long):,}")


if __name__ == "__main__":
    load()