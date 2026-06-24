import pygame

from config import RESOURCE_SIZE


class ResourceSource:
    def __init__(self, x: float, y: float, amount: int = 70) -> None:
        self.x = x
        self.y = y
        self.amount = amount
        self.max_amount = amount
        self.size = RESOURCE_SIZE

    def take_resource(self, amount: int) -> int:
        taken = min(amount, self.amount)
        self.amount -= taken
        return taken

    def is_empty(self) -> bool:
        return self.amount <= 0

    def draw(self, surface) -> None:
        color = (115, 145, 165) if not self.is_empty() else (85, 95, 100)
        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = (int(self.x), int(self.y))
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, (45, 65, 75), rect, 2)
