import pygame

from config import FOOD_SIZE


FOOD_SOURCE_TYPES = {
    "small_berries": {
        "min_amount": 90,
        "max_amount": 140,
        "carry_yield": 1,
        "regen_ticks": 900,
        "regen_amount": 1,
        "color": (55, 170, 70),
    },
    "rich_fungus": {
        "min_amount": 120,
        "max_amount": 190,
        "carry_yield": 2,
        "regen_ticks": 1800,
        "regen_amount": 1,
        "color": (70, 145, 210),
    },
    "sap_tree": {
        "min_amount": 170,
        "max_amount": 260,
        "carry_yield": 3,
        "regen_ticks": 3200,
        "regen_amount": 1,
        "color": (210, 165, 70),
    },
}


class FoodSource:
    def __init__(self, x: float, y: float, source_type: str = "small_berries", amount: int | None = None) -> None:
        self.x = x
        self.y = y
        self.source_type = source_type
        self.type_config = FOOD_SOURCE_TYPES[source_type]
        starting_amount = amount if amount is not None else self.type_config["max_amount"]
        self.amount = starting_amount
        self.max_amount = starting_amount
        self.size = FOOD_SIZE
        self.discovered = False
        self.carry_yield = self.type_config["carry_yield"]
        self.regen_ticks = self.type_config["regen_ticks"]
        self.regen_amount = self.type_config["regen_amount"]
        self._regen_progress = 0

    def take_food(self, amount: int) -> int:
        taken = min(amount, self.amount)
        self.amount -= taken
        return taken

    def update(self) -> None:
        if self.is_empty():
            self._regen_progress = 0
            return

        if self.amount >= self.max_amount:
            self._regen_progress = 0
            return

        self._regen_progress += 1
        if self._regen_progress >= self.regen_ticks:
            self._regen_progress = 0
            self.amount = min(self.max_amount, self.amount + self.regen_amount)

    def is_empty(self) -> bool:
        return self.amount <= 0

    def reserve_ratio(self) -> float:
        if self.max_amount <= 0:
            return 0.0
        return self.amount / self.max_amount

    def draw(self, surface) -> None:
        if not self.discovered:
            return

        color = self.type_config["color"] if not self.is_empty() else (90, 100, 90)
        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (25, 65, 25), rect, 2)
