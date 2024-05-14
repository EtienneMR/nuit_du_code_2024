import pyxel

GRAVITE = 0.25  # accélération en pixel par frame
VITESSE = 1
SAUT = 4
ANIM_SPEED = 4

MAP_SIZE = 16 * 8


def get_block(app: "App", x: float, y: float) -> tuple:
    return app.tilemap.pget((x + app.map_x) // 8, y // 8)


def is_wall(block: tuple, semi_collide: bool) -> bool:
    obj_x, obj_y = block
    return obj_y > 25 or (semi_collide and obj_y == 25 and obj_x >= 3)


def unit(nb: float) -> int:
    if nb == 0:
        return 0
    else:
        return nb / abs(nb)


class EntiteePhysique:
    def __init__(self, app: "App"):
        self.x = 0
        self.y = 0
        self.dx = 0
        self.dy = 0
        self.app = app
        self.size = 8
        self.right = True

    def update(self):
        half_size = self.size // 2
        # Vertical

        if is_wall(
            get_block(
                self.app,
                self.x + half_size + self.dx + unit(self.dx) * half_size,
                self.y + half_size + unit(self.dy) * half_size,
            ),
            self.dy > 0,
        ):
            self.dx = 0

        if self.dx > 0:
            self.right = True
        elif self.dx < 0:
            self.right = False

        # Horizontal

        if is_wall(
            get_block(
                self.app,
                self.x + half_size + unit(self.dx) * half_size,
                self.y + self.dy + half_size + unit(self.dy) * half_size,
            ),
            self.dy > 0,
        ):
            self.dy = 0

        self.dx = min(max(self.dx, -self.x), MAP_SIZE - self.x - self.size)
        self.dy = max(self.dy, -self.y)

        if self.dx > 0:
            self.right = True
        elif self.dx < 0:
            self.right = False

        self.x += self.dx
        self.y += self.dy


class Joueur(EntiteePhysique):
    def __init__(self, app: "App"):
        super().__init__(app)
        self.attacking = True
        self.size = 8
        self.piece = 0
        self.etoile = 0
        self.last_dy = 0
        self.respawn_x = 0
        self.respawn_y = 0
        self.respawn_piece = 0
        self.respawn_etoile = 0
        self.anim_frame = 0
        self.y = MAP_SIZE - 5 * 8
        self.skin = False

    def update(self):
        # Vertical
        ndx = 0
        if pyxel.btn(pyxel.KEY_LEFT):
            ndx -= VITESSE
        if pyxel.btn(pyxel.KEY_RIGHT):
            ndx += VITESSE
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.skin = not self.skin

        # Horizontal
        ay = 0
        if self.dy == 0 and self.last_dy == 0 and pyxel.btn(pyxel.KEY_UP):
            ay -= SAUT * (1 if self.skin else 0.75)
        else:
            ay += GRAVITE

        if self.attacking:
            if self.anim_frame > ANIM_SPEED * 3:
                self.attacking = False
                self.anim_frame = 0
            elif not self.skin:
                ndx += unit(ndx) * 2
        elif not self.attacking and pyxel.btn(pyxel.KEY_SPACE):
            self.attacking = True
            self.anim_frame = 0

        self.dx = ndx
        self.last_dy = self.dy
        self.dy += ay

        super().update()

        block = get_block(self.app, self.x, self.y)

        if block == (17, 0):
            self.x = MAP_SIZE - self.x
            self.app.update_map_id(self.app.map_id + 1)
            self.respawn_x = self.x
            self.respawn_y = self.y
            self.respawn_piece = self.piece
            self.respawn_etoile = self.etoile

        if self.y > MAP_SIZE:
            self.kill()

        self.anim_frame += 1

    def draw(self):
        u = 1
        v = 1
        if self.attacking:
            v = 1
            if self.right:
                u = self.anim_frame // ANIM_SPEED % 3
            else:
                u = 3 + self.anim_frame // ANIM_SPEED % 3
        else:
            v = 2 if self.right else 3

            if self.dx == 0:
                u = 0
            else:
                u = (self.anim_frame // ANIM_SPEED) % 9

        if self.skin:
            v += 3

        pyxel.blt(self.x, self.y, 0, u * 8, v * 8, 8, 8, 5)

    def kill(self):
        self.app.update_map_id(self.app.map_id)
        self.x = self.respawn_x
        self.y = self.respawn_y
        self.piece = self.respawn_piece
        self.etoile = self.respawn_etoile


class Piece:
    def __init__(self, app: "App", x: float, y: float):
        self.x = x
        self.y = y
        self.app = app
        self.piece_recup = False

    def update(self):
        if (
            abs(self.app.joueur.x - self.x) + abs(self.app.joueur.y - self.y) < 8
            and not self.piece_recup
        ):
            self.piece_recup = True
            self.app.joueur.piece += 1

    def draw(self):
        u = 32 + (pyxel.frame_count // ANIM_SPEED) % 4 * 8
        v = 160
        if not self.piece_recup:
            pyxel.blt(self.x, self.y, 0, u, v, 8, 8, 5)


class Coffre:
    def __init__(self, app: "App", x: float, y: float):
        self.x = x
        self.y = y
        self.app = app
        self.etoile_recup = False
        self.anim_frame = 0

    def update(self):
        if (
            abs(self.app.joueur.x - self.x) + abs(self.app.joueur.y - self.y) < 6
            and not self.etoile_recup
        ):
            self.etoile_recup = True
            self.app.joueur.etoile += 1
        elif self.etoile_recup:
            self.anim_frame += 1

    def draw(self):
        if not self.etoile_recup:
            pyxel.blt(self.x, self.y, 0, 8, 160, 8, 8, 5)
        elif self.anim_frame < 15 * ANIM_SPEED:
            pyxel.blt(self.x, self.y - 8, 0, 16, 192, 8, 8, 5)


class Ressort:
    def __init__(self, app: "App", x: float, y: float):
        self.x = x
        self.y = y
        self.app = app
        self.anim_frame = 0

    def update(self):
        if (
            abs(self.app.joueur.x - self.x) + abs(self.app.joueur.y - self.y) < 8
            and self.anim_frame == 0
        ):
            self.anim_frame = 1
            self.app.joueur.dy -= 6
        elif self.anim_frame != 0:
            self.anim_frame += 1
            if self.anim_frame >= 3 * ANIM_SPEED:
                self.anim_frame = 0

    def draw(self):
        pyxel.blt(
            self.x, self.y, 0, 32 + self.anim_frame // ANIM_SPEED * 8, 176, 8, 8, 5
        )


class Araignee(EntiteePhysique):

    def __init__(self, app: "App", x: float, y: float):
        self.app = app
        super().__init__(app)
        self.x = x
        self.y = y
        self.dead = False

    def update(self):
        if not self.dead:
            if self.dx == 0:
                self.dx = 1

            if not is_wall(
                get_block(
                    self.app,
                    self.x + self.size // 2 + self.dx,
                    self.y + self.size // 2 + 1 * 8,
                ),
                True,
            ):
                self.dx *= -1
            super().update()

            if abs(self.app.joueur.x - self.x) + abs(self.app.joueur.y - self.y) < 8:
                if self.app.joueur.attacking:
                    self.dead = True
                else:
                    self.app.joueur.kill()

    def draw(self):
        if not self.dead:
            u = ((0 if self.right else 4) + (pyxel.frame_count // ANIM_SPEED) % 4) * 8
            v = 152
            pyxel.blt(self.x, self.y, 0, u, v, 8, 8, 5)


# class


class App:
    def __init__(self):
        pyxel.init(
            128, 128, title="Nuit du code", capture_scale=4, quit_key=pyxel.KEY_Q
        )
        pyxel.load("res.pyxres")

        self.joueur = Joueur(self)
        self.tilemap = pyxel.tilemaps[0]
        self.map_id = 0
        self.entititees = []
        self.entititees_pos = []

        self.update_map_id(0)

        pyxel.playm(0, loop=True)
        pyxel.run(self.update, self.draw)

    @property
    def map_x(self):
        return self.map_id * MAP_SIZE

    def update_map_id(self, new: int):
        self.entititees.clear()
        self.entititees_pos.clear()
        self.map_id = new

        for x in range(0, MAP_SIZE, 8):
            for y in range(0, MAP_SIZE, 8):
                block = get_block(self, x, y)

                if block == (4, 20):
                    self.entititees.append(Piece(self, x, y))
                    self.entititees_pos.append((x, y))
                elif block == (0, 19):
                    self.entititees.append(Araignee(self, x, y))
                    self.entititees_pos.append((x, y))
                elif block == (4, 22):
                    self.entititees.append(Ressort(self, x, y))
                    self.entititees_pos.append((x, y))
                elif block == (1, 20):
                    self.entititees.append(Coffre(self, x, y))
                    self.entititees_pos.append((x, y))

    def update(self):
        for entitee in self.entititees:
            entitee.update()
        self.joueur.update()

    def draw(self):
        pyxel.cls(12)
        pyxel.bltm(0, 0, self.tilemap, self.map_x, 0, MAP_SIZE, MAP_SIZE, 5)
        for entitee_pos in self.entititees_pos:
            pyxel.rect(entitee_pos[0], entitee_pos[1], 8, 8, 12)
        for entitee in self.entititees:
            entitee.draw()
        self.joueur.draw()

        pyxel.blt(
            0,
            0,
            0,
            32 + (pyxel.frame_count // ANIM_SPEED) % 4 * 8,
            160,
            8,
            8,
            5,
        )
        pyxel.text(10, 2, str(self.joueur.piece), 0)

        pyxel.blt(
            20,
            0,
            0,
            16,
            192,
            8,
            8,
            5,
        )
        pyxel.text(30, 2, str(self.joueur.etoile), 0)

        if self.map_id == 6:
            pyxel.text((MAP_SIZE - 20) // 2, (MAP_SIZE - 6) // 2, "Bravo !", 8)


App()
