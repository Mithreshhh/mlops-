from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Int64

student = Entity(
    name="student",
    join_keys=["student_id"],
    description="A unique student identifier",
)

student_source = FileSource(
    name="student_source",
    path="../../data/student_features.parquet",
    timestamp_field="event_timestamp",
)

student_features = FeatureView(
    name="student_features",
    entities=[student],
    ttl=timedelta(days=365),
    schema=[
        Field(name="studytime", dtype=Int64),
        Field(name="failures", dtype=Int64),
        Field(name="absences", dtype=Int64),
        Field(name="G1", dtype=Int64),
        Field(name="G2", dtype=Int64),
    ],
    source=student_source,
    online=True,
)
