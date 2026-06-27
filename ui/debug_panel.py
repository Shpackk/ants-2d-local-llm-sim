import pygame


class DebugPanel:
    def __init__(self) -> None:
        self.font = pygame.font.Font(None, 24)

    def draw(self, surface, world, colony, fps: float) -> None:
        state = colony.get_state_summary(world)
        status = "RUNNING"
        if colony.goal_reached:
            status = "GOAL REACHED"
        elif colony.lost:
            status = f"LOST: {colony.loss_reason}"

        lines = [
            "Ant Colony Simulation - LLM Challenge",
            f"Status: {status}",
            f"Tick: {world.tick_count}",
            f"Goal: {state['living_ants']}/{state['target_ants']} living ants",
            f"Food Storage: {colony.food_storage}",
            f"Eggs: {len(colony.eggs)}",
            f"Workers: {colony.get_worker_count()}",
            f"Exploring: {state['workers_exploring']}",
            f"Stale Explorers: {state['workers_exploring_too_long']}",
            f"Foraging: {state['workers_foraging']}",
            f"Returning Food: {state['workers_returning_with_food']}",
            f"Food Available Workers: {state['workers_available_for_food']}",
            f"Known Food: {state['known_food_available_sources']}/{state['known_food_sources']} ({state['known_food_remaining']}/{state['known_food_capacity']})",
            f"Depleted Food: {state['known_food_depleted_sources']}",
            f"Deaths: {colony.deaths}",
            f"Nest Health: {colony.nest_health}/{colony.max_nest_health}",
            f"Resource Storage: {colony.resource_storage}",
            f"Warriors: {colony.get_warrior_count()}",
            f"Threats: {len(world.threats)}",
            f"Workers carrying food: {colony.workers_carrying_food()}",
            f"FPS: {fps:.0f}",
        ]

        panel_rect = pygame.Rect(10, 10, 380, 480)
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surface.fill((20, 25, 20, 185))
        surface.blit(panel_surface, panel_rect)

        for index, line in enumerate(lines):
            text = self.font.render(line, True, (235, 240, 220))
            surface.blit(text, (22, 22 + index * 23))
