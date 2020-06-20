<template>
  <div
    ref="snake"
    tabindex="-1"
    class="Snake"

    @keyup.w="handleKeys({ name: 'one', side: 'stepTop' })"
    @keyup.d="handleKeys({ name: 'one', side: 'stepRight' })"
    @keyup.s="handleKeys({ name: 'one', side: 'stepBottom' })"
    @keyup.a="handleKeys({ name: 'one', side: 'stepLeft' })"

    @keyup.up="handleKeys({ name: 'two', side: 'stepTop' })"
    @keyup.right="handleKeys({ name: 'two', side: 'stepRight' })"
    @keyup.down="handleKeys({ name: 'two', side: 'stepBottom' })"
    @keyup.left="handleKeys({ name: 'two', side: 'stepLeft' })"
  >
    <div class="field">
      <div
        v-for="(color, colorIndex) in field"
        :key="colorIndex"
        :style="{ backgroundColor: color }"
        class="cell"
      >
        {{ actors.one.rewards[colorIndex] }}
        {{ actors.two.rewards[colorIndex] }}
      </div>
    </div>

    <div class="actors field">
      <div
        v-for="actor in Object.values(actors)"
        :key="actor.id"
      >
        <div
          v-for="cell in actor.cells"
          :key="cell.id"
          :style="{
            gridColumn: cell.position.x,
            gridRow: cell.position.y,
            backgroundColor: actor.color,
          }"
        />
      </div>
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';
import { nanoid } from 'nanoid';
import cloneDeep from 'clone-deep';

const fieldSize = 25;

const actorOneHeadColor = 'rgba(201, 52, 65, 1.0)';
const actorOneTailColor = 'rgba(201, 52, 65, 0.5)';

const actorTwoHeadColor = 'rgba(34, 95, 228, 1.0)';
const actorTwoTailColor = 'rgba(34, 95, 228, 0.5)';

const basicColor = '#222';
const barrierColor = '#111';
const appleColor = 'green';

const basicReward = 0.1;
// const barrierReward = -1;
// const appleReward = 1;

const numberSides = 4;
const autoMovementDelay = 500;

const colors = [
  actorOneHeadColor,
  actorOneTailColor,

  actorTwoHeadColor,
  actorTwoTailColor,

  barrierColor,
];

const sides = {
  0: 'stepTop',
  1: 'stepRight',
  2: 'stepBottom',
  3: 'stepLeft',
};

let nextFrameId = -1;

// todo переключение режимов (mode), чтобы играть против МЛ вручную и потом возобновить обучение.

export default {
  name: 'Snake',

  data() {
    return {
      field: Array(fieldSize ** 2).fill(basicColor),
      fieldDefault: undefined,
      fieldSize,

      actors: {
        one: {
          id: nanoid(),
          name: 'one',
          side: 'stepBottom',
          model: tf.sequential(),
          training: { inputs: [], labels: [] },
          rewards: Array(numberSides).fill(basicReward),
          colorHead: colors[0],
          colorTail: colors[1],
          cells: [
            { id: nanoid(), position: { x: 3, y: 5 } },
            { id: nanoid(), position: { x: 3, y: 4 } },
            { id: nanoid(), position: { x: 3, y: 3 } },
          ],
        },
        two: {
          id: nanoid(),
          name: 'two',
          side: 'stepTop',
          model: tf.sequential(),
          training: { inputs: [], labels: [] },
          rewards: Array(numberSides).fill(basicReward),
          colorHead: colors[2],
          colorTail: colors[3],
          cells: [
            { id: nanoid(), position: { x: fieldSize - 4, y: fieldSize - 9 } },
            { id: nanoid(), position: { x: fieldSize - 4, y: fieldSize - 8 } },
            { id: nanoid(), position: { x: fieldSize - 4, y: fieldSize - 7 } },
            { id: nanoid(), position: { x: fieldSize - 4, y: fieldSize - 6 } },
            { id: nanoid(), position: { x: fieldSize - 4, y: fieldSize - 5 } },
            { id: nanoid(), position: { x: fieldSize - 4, y: fieldSize - 4 } },
          ],
        },
      },
      actorsDefault: undefined,

      mode: 'gaming', // training | gaming
    };
  },

  mounted() {
    this.setFieldSize();

    this.actorsDefault = cloneDeep(this.actors);
    Object.values(this.actors).forEach(this.setupModel);

    this.initialField();
    this.initialActors();
    this.addApple();

    this.runGame();
  },

  methods: {
    // Игровой алгоритм.
    setFieldSize() {
      this.$refs.snake.style.setProperty('--rows', String(fieldSize));
      this.$refs.snake.style.setProperty('--columns', String(fieldSize));
    },

    initialField() {
      for (let x = 0; x < fieldSize; x += 1) {
        for (let y = 0; y < fieldSize; y += 1) {
          const isBarrier = x === 0 || x === fieldSize - 1 || y === 0 || y === fieldSize - 1;
          const color = isBarrier ? barrierColor : basicColor;
          const cellIndex = y * fieldSize + x;

          this.field[cellIndex] = color;
        }
      }

      this.fieldDefault = cloneDeep(this.field);
    },

    initialActors() {
      Object.values(this.actors).forEach((actor) => {
        actor.cells.forEach(({ position: { x, y } }, actorCellIndex) => {
          const cellIndex = y * fieldSize + x;
          this.field[cellIndex] = actorCellIndex === 0 ? actor.colorHead : actor.colorTail;
        });

        actor.rewards = actor.rewards.map(() => basicReward);
      });
    },

    addApple() {
      const appleCellIndex = Math.round(Math.random() * (this.field.length - 1));

      if (this.field[appleCellIndex] === basicColor) {
        this.field[appleCellIndex] = appleColor;
      } else {
        this.addApple();
      }
    },

    runGame() {
      if (this.mode === 'training') {
        nextFrameId = requestAnimationFrame(this.autoStep);
      } else if (this.mode === 'gaming') {
        nextFrameId = setTimeout(this.autoStep, autoMovementDelay);
      }
    },

    handleKeys({ name, side }) {
      if (this.mode === 'gaming') {
        this.actors[name].side = side;
      }
    },

    async autoStep() {
      await Promise.all(Object.values(this.actors).map((actor) => (async () => {
        this.estimationSides(actor);

        // 0 - stepTop, 1 - stepRight, 2 - stepBottom, 3 - stepLeft.
        const sideIndex = await this.modelPredict(actor);
        actor.side = sides[sideIndex];

        const { name, side } = actor;
        this.step({ name, side });
      })()));

      nextFrameId = setTimeout(this.autoStep, autoMovementDelay);
    },

    step({ name, side }) {
      const actor = this.actors[name];

      this.clearTail(actor);
      this.stepTail(actor);
      this.stepHead({ actor, side });
    },

    clearTail(actor) {
      const { position: { x, y } } = actor.cells[actor.cells.length - 1];

      const cellIndex = y * fieldSize + x;
      this.field[cellIndex] = basicColor;
    },

    stepTail(actor) {
      for (let i = actor.cells.length - 1; i > 0; i -= 1) {
        const cell = actor.cells[i];
        cell.position = actor.cells[i - 1].position;

        const { position: { x, y } } = cell;
        const cellIndex = y * fieldSize + x;

        this.field[cellIndex] = actor.colorTail;
      }
    },

    stepHead({ actor, side }) {
      const [headCell] = actor.cells;
      const { position: { x: xHead, y: yHead } } = headCell;

      this[side]({ headCell, x: xHead, y: yHead });

      this.nextCell(actor);
    },

    stepTop({ headCell, x, y }) {
      headCell.position = { x, y: y - 1 };
    },

    stepRight({ headCell, x, y }) {
      headCell.position = { x: x + 1, y };
    },

    stepBottom({ headCell, x, y }) {
      headCell.position = { x, y: y + 1 };
    },

    stepLeft({ headCell, x, y }) {
      headCell.position = { x: x - 1, y };
    },

    nextCell(actor) {
      const [{ position: { x, y } }] = actor.cells;
      const nextCellIndex = y * fieldSize + x;
      const nextColor = this.field[nextCellIndex];

      if (colors.includes(nextColor)) {
        this.gameOver(actor);
      } else {
        this.field[nextCellIndex] = actor.colorHead;

        if (nextColor === appleColor) {
          this.growth({ actor, x, y });
          this.addApple();
        }
      }
    },

    growth({ actor, x, y }) {
      actor.cells.push({ id: nanoid(), position: { x, y } });
    },

    // todo остановить игру, пока идёт обучение
    gameOver(actor) {
      cancelAnimationFrame(nextFrameId);
      clearTimeout(nextFrameId);
      nextFrameId = -1;

      this.field = cloneDeep(this.fieldDefault);
      this.actors = cloneDeep(this.actorsDefault);

      this.initialActors();
      this.addApple();

      console.log('game over:', actor.name);
      // todo обучение моделей. fit

      // this.runGame();
    },

    // ML алгоритм.
    setupModel({ model }) {
      model.add(tf.layers.dense({
        inputShape: [numberSides],
        activation: 'sigmoid',
        units: 128,
      }));

      // model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 128,
      // }));

      model.add(tf.layers.dense({
        activation: 'sigmoid',
        units: numberSides,
      }));

      model.compile({
        optimizer: 'adam',
        loss: 'meanSquaredError',
      });
    },

    // todo алгоритм оценки 4 сторон
    // todo врага так же разметить как -1 (стена). отметить всех и себя тоже
    // todo яблоко +1 для стороны
    estimationSides(actor) {
      // actor.rewards
    },

    searchApples() {},

    async modelPredict(actor) {
      const predictions = await actor.model.predict(tf.tensor2d([actor.rewards])).data();
      return predictions.indexOf(Math.max(...predictions));
    },

    // todo алгоритм оценки текущего положения и куда лучше сходить, после чего, ML выберет ход.
    // actor.rewards[nextColor] = barrierReward;
    // actor.rewards[nextColor] = appleReward;
  },
};
</script>

<style
  lang="scss"
  scoped
>
.Snake {
  --rows: -1;
  --columns: -1;
  --size: 30px;

  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  user-select: none;
  outline: none;
}

.field {
  display: grid;
  grid-template-rows: repeat(var(--rows), var(--size));
  grid-template-columns: repeat(var(--columns), var(--size));

  .cell {
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 12px;
    color: #555;
  }
}

.actors {
  position: absolute;
}
</style>
