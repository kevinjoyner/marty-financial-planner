from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Any
from app import models, schemas

@dataclass
class ProjectionContext:
    month_start: date
    account_balances: Dict[int, int]
    account_book_costs: Dict[int, int]
    flows: Dict[int, Any]
    ytd_contributions: Dict = field(default_factory=dict)
    ytd_earnings: Dict = field(default_factory=dict)
    ytd_interest: Dict = field(default_factory=dict)
    ytd_gains: Dict = field(default_factory=dict)
    warnings: List = field(default_factory=list)
    rule_logs: List = field(default_factory=list)
    mortgage_state: Dict = field(default_factory=dict)
    mortgage_stats: List = field(default_factory=list)
    annotations: List = field(default_factory=list)
    all_accounts: List[models.Account] = field(default_factory=list)
    prev_balances: Dict[int, int] = field(default_factory=dict)
