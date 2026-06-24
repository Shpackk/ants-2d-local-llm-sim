import pygame

from ui.debug_panel import DebugPanel


class Renderer:
    def __init__(self) -> None:
        self.debug_panel = DebugPanel()

    def draw_world(self, surface, world, colony, fps: float = 0.0) -> None:
        self.draw_background(surface)
        self.draw_nest(surface, world, colony)

        for food_source in world.food_sources:
            food_source.draw(surface)

        for resource_source in world.resource_sources:
            resource_source.draw(surface)

        for threat in world.threats:
            threat.draw(surface)

        if colony.queen:
            colony.queen.draw(surface)

        for worker in colony.workers:
            worker.draw(surface)

        for warrior in colony.warriors:
            warrior.draw(surface)

        self.debug_panel.draw(surface, world, colony, fps)

    def draw_background(self, surface) -> None:
        surface.fill((58, 74, 43))

    def draw_nest(self, surface, world, colony) -> None:
        pygame.draw.circle(
            surface,
            (116, 72, 37),
            (int(world.nest_x), int(world.nest_y)),
            world.nest_radius,
        )
        pygame.draw.circle(
            surface,
            (68, 42, 21),
            (int(world.nest_x), int(world.nest_y)),
            world.nest_radius,
            3,
        )
        self.draw_healthbar(
            surface,
            world.nest_x - 45,
            world.nest_y - world.nest_radius - 18,
            90,
            8,
            colony.nest_health,
            colony.max_nest_health,
        )

    def draw_healthbar(self, surface, x, y, width, height, health, max_health) -> None:
        ratio = health / max_health if max_health else 0
        pygame.draw.rect(surface, (70, 20, 20), (int(x), int(y), width, height))
        pygame.draw.rect(surface, (70, 190, 75), (int(x), int(y), int(width * ratio), height))
        pygame.draw.rect(surface, (25, 25, 20), (int(x), int(y), width, height), 1)
