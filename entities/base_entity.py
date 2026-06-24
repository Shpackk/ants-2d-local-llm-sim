import math


class BaseEntity:
    def __init__(self, x: float, y: float, radius: int) -> None:
        self.x = x
        self.y = y
        self.radius = radius
        self.is_alive = True

    def update(self, world, colony) -> None:
        pass

    def draw(self, surface) -> None:
        pass

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(self.x - x, self.y - y)

    def move_toward(self, target_x: float, target_y: float, speed: float) -> bool:
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance <= speed or distance == 0:
            self.x = target_x
            self.y = target_y
            return True

        self.x += (dx / distance) * speed
        self.y += (dy / distance) * speed
        return False

    def apply_separation(self, entities, min_distance: float, strength: float, world=None) -> None:
        push_x = 0.0
        push_y = 0.0

        for entity in entities:
            if entity is self:
                continue

            dx = self.x - entity.x
            dy = self.y - entity.y
            distance = math.hypot(dx, dy)
            if distance == 0:
                dx = 1.0
                dy = 0.0
                distance = 1.0

            if distance < min_distance:
                pressure = (min_distance - distance) / min_distance
                push_x += (dx / distance) * pressure
                push_y += (dy / distance) * pressure

        self.x += push_x * strength
        self.y += push_y * strength

        if world is not None:
            self.x = max(self.radius, min(world.width - self.radius, self.x))
            self.y = max(self.radius, min(world.height - self.radius, self.y))
