from concurrent.futures import ThreadPoolExecutor

import pygame

from colony import Colony
from config import FPS, MAX_SIMULATION_TICKS, SCREEN_HEIGHT, SCREEN_WIDTH
from llm_controller import LLMQueenController
from stats_recorder import GameStatsRecorder
from ui.renderer import Renderer
from world import World


JAN_MODEL_NAME = "Qwen3_5-9B-Q5_K_M"
QUEEN_INTERVAL_SECONDS = 5


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Ant Colony Simulation - LLM Challenge")
    clock = pygame.time.Clock()

    world = World()
    colony = Colony()
    renderer = Renderer()
    queen_controller = LLMQueenController(model_name=JAN_MODEL_NAME)
    stats_recorder = GameStatsRecorder(model_name=JAN_MODEL_NAME)
    queen_executor = ThreadPoolExecutor(max_workers=1)
    queen_future = None
    queen_timer = 0.0
    stats_saved = False

    world.seed_world()
    colony.seed_colony(world)
    stats_recorder.record_snapshot(world, colony)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        colony.update(world)
        world.update(colony)

        if world.tick_count >= MAX_SIMULATION_TICKS and not colony.goal_reached and not colony.lost:
            colony.lost = True
            colony.loss_reason = "max ticks reached"

        if queen_future is not None and queen_future.done():
            command = queen_future.result()
            queen_future = None
            if not colony.goal_reached and not colony.lost:
                stats_recorder.record_queen_command(world.tick_count, command)
                colony.execute_queen_command(command)

        dt = clock.get_time() / 1000.0
        queen_timer += dt
        if queen_timer >= QUEEN_INTERVAL_SECONDS and queen_future is None and not colony.goal_reached and not colony.lost:
            queen_timer = 0.0
            colony_state = colony.get_state_summary(world)
            queen_future = queen_executor.submit(queen_controller.decide, colony_state)

        stats_recorder.record_if_due(world, colony)
        if (colony.goal_reached or colony.lost) and not stats_saved:
            stats_path = stats_recorder.save(world, colony)
            print(f"[Stats] Saved {stats_path}")
            stats_saved = True

        fps = clock.get_fps()
        renderer.draw_world(screen, world, colony, fps)
        pygame.display.flip()
        clock.tick(FPS)

    queen_executor.shutdown(wait=False, cancel_futures=True)
    pygame.quit()


if __name__ == "__main__":
    main()
