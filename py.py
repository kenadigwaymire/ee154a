```@dataclass(frozen=True)
class Obs:
    """
    Common signature for Logging + BigQuery.

    Conventions used by BigQueryEmitter routing:
      - steps table:       name="step",       action="end"
      - experiments table: name="experiment", action="end"
      - events table:      everything else

    Tracing is intentionally separate and NOT driven by Obs.
    """
    name: str
    action: str = "emit"
    key: Optional[str] = None

    run_id: Optional[str] = None
    experiment_id: Optional[str] = None

    model: Optional[str] = None
    dataset: Optional[str] = None
    phase: Optional[str] = None
    step_index: Optional[int] = None

    ts: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_s: Optional[float] = None

    success: Optional[bool] = None
    failure_mode: Optional[str] = None

    cost_usd: Optional[float] = None
    api_calls: Optional[int] = None

    metrics: Mapping[str, Any] = field(default_factory=dict)
    attrs: Mapping[str, Any] = field(default_factory=dict)

    severity: str = "INFO"
    labels: Mapping[str, str] = field(default_factory=dict)```
