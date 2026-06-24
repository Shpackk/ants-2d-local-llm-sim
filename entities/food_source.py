import pygame

from config import FOOD_SIZE


class FoodSource:
    def __init__(self, x: float, y: float, amount: int = 50) -> None:
        self.x = x
        self.y = y
        self.amount = amount
        self.max_amount = amount
        self.size = FOOD_SIZE

    def take_food(self, amount: int) -> int:
        taken = min(amount, self.amount)
        self.amount -= taken
        return taken

    def is_empty(self) -> bool:
        return self.amount <= 0

    def draw(self, surface) -> None:
        color = (55, 170, 70) if not self.is_empty() else (90, 100, 90)
        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (25, 65, 25), rect, 2)
