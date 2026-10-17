"""Provider-reported usage, immutable request prices and rolling cost totals."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

MILLION = Decimal(1_000_000)
WINDOWS = (("近1天", 1), ("近3天", 3), ("近7天", 7), ("近30天", 30), ("总计", None))


@dataclass(frozen=True)
class UsageContext:
    platform: str
    bot: str
    actor: str
    group: str
    operation: str

    @classmethod
    def from_command(cls, ctx, operation, *, group=None):
        return cls(
            ctx.platform,
            ctx.bot,
            ctx.actor,
            ctx.group if group is None else group,
            operation,
        )


@dataclass(frozen=True)
class TokenUsage:
    input: int | None = None
    output: int | None = None
    total: int | None = None

    @classmethod
    def parse(cls, value):
        if not isinstance(value, dict):
            return cls()

        def count(name):
            number = value.get(name)
            return number if type(number) is int and 0 <= number < 2**63 else None

        incoming, outgoing, total = (
            count("input_tokens"),
            count("output_tokens"),
            count("total_tokens"),
        )
        if total is None and incoming is not None and outgoing is not None:
            combined = incoming + outgoing
            total = combined if combined < 2**63 else None
        return cls(incoming, outgoing, total)

    @property
    def complete(self):
        return self.input is not None and self.output is not None


@dataclass(frozen=True)
class TokenPrices:
    input: Decimal
    output: Decimal

    @classmethod
    def from_config(cls, config):
        def price(name):
            value = config.get(name, 0)
            try:
                amount = Decimal(str(value))
            except (InvalidOperation, ValueError) as exc:
                raise ValueError("Token 单价必须为非负的有限人民币金额。") from exc
            if not amount.is_finite() or amount < 0:
                raise ValueError("Token 单价必须为非负的有限人民币金额。")
            return amount

        return cls(
            price("input_price_per_million_cny"),
            price("output_price_per_million_cny"),
        )

    def costs(self, tokens):
        return (
            None if tokens.input is None else self.input * tokens.input / MILLION,
            None if tokens.output is None else self.output * tokens.output / MILLION,
        )


@dataclass
class UsageTotals:
    requests: int = 0
    input: int = 0
    output: int = 0
    total: int = 0
    cost: Decimal = Decimal(0)
    unknown: int = 0
    pending: int = 0

    def add(self, tokens, input_cost, output_cost, state):
        self.requests += 1
        self.input += tokens.input or 0
        self.output += tokens.output or 0
        self.total += (
            tokens.total
            if tokens.total is not None
            else (tokens.input or 0) + (tokens.output or 0)
        )
        self.cost += (input_cost or Decimal(0)) + (output_cost or Decimal(0))
        self.unknown += not tokens.complete
        self.pending += state == "pending"


def empty_windows():
    return [UsageTotals() for _ in WINDOWS]


@dataclass
class CostReport:
    started_at: float
    total: list[UsageTotals] = field(default_factory=empty_windows)
    accounts: dict[str, list[UsageTotals]] = field(default_factory=dict)
    groups: dict[str, list[UsageTotals]] = field(default_factory=dict)
