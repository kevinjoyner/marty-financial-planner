from typing import Annotated
from decimal import Decimal

# Money is always stored as Integer Pence (e.g. £10.50 -> 1050)
Money = Annotated[int, "Pence"]

# Rates are stored as Decimal for precision (e.g. 5.5% -> 5.5)
# When using in calculation, remember to divide by 100 if it's a percentage
Rate = Annotated[Decimal, "Multiplier"]
