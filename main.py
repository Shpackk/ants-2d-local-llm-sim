from concurrent.futures import ThreadPoolExecutor

import pygame

from colony import Colony
from config import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from llm_controller import LLMQueenController
from ui.renderer import Renderer
from world import World


JAN_MODEL_NAME = "Qwen3_5-4B-IQ4_XS"
QUEEN_INTERVAL_SECONDS = 20


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Ant Colony Simulation - Phase 1")
    clock = pygame.time.Clock()

    world = World()
    colony = Colony()
    renderer = Renderer()
    queen_controller = LLMQueenController(model_name=JAN_MODEL_NAME)
    queen_executor = ThreadPoolExecutor(max_workers=1)
    queen_future = None
    queen_timer = 0.0

    world.seed_world()
    colony.seed_colony(world)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        colony.update(world)
        world.update(colony)

        if queen_future is not None and queen_future.done():
            command = queen_future.result()
            queen_future = None
            colony.execute_queen_command(command)

        dt = clock.get_time() / 1000.0
        queen_timer += dt
        if queen_timer >= QUEEN_INTERVAL_SECONDS and queen_future is None:
            queen_timer = 0.0
            colony_state = colony.get_state_summary(world)
            queen_future = queen_executor.submit(queen_controller.decide, colony_state)

        fps = clock.get_fps()
        renderer.draw_world(screen, world, colony, fps)
        pygame.display.flip()
        clock.tick(FPS)

    queen_executor.shutdown(wait=False, cancel_futures=True)
    pygame.quit()


if __name__ == "__main__":
    main()
