import pygame


class DebugPanel:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 24)

    def draw(self, surface, world, colony, fps: float) -> None:
        lines = [
            "Ant Colony Simulation - Phase 1",
            f"Nest Health: {colony.nest_health}/{colony.max_nest_health}",
            f"Food Storage: {colony.food_storage}",
            f"Resource Storage: {colony.resource_storage}",
            f"Workers: {colony.get_worker_count()}",
            f"Warriors: {colony.get_warrior_count()}",
            f"Food Sources: {len(world.food_sources)}",
            f"Resource Sources: {len(world.resource_sources)}",
            f"Threats: {len(world.threats)}",
            f"Workers carrying food: {colony.workers_carrying_food()}",
            f"Workers carrying resources: {colony.workers_carrying_resources()}",
            f"FPS: {fps:.0f}",
        ]

        panel_rect = pygame.Rect(10, 10, 330, 300)
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surface.fill((20, 25, 20, 185))
        surface.blit(panel_surface, panel_rect)

        for index, line in enumerate(lines):
            text = self.font.render(line, True, (235, 240, 220))
            surface.blit(text, (22, 22 + index * 23))
