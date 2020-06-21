<template>
  <div
    ref="snake"
    tabindex="-1"
    class="Snake"

    @keyup.w="handleKeys({ name: 'human', side: 'stepTop' })"
    @keyup.d="handleKeys({ name: 'human', side: 'stepRight' })"
    @keyup.s="handleKeys({ name: 'human', side: 'stepBottom' })"
    @keyup.a="handleKeys({ name: 'human', side: 'stepLeft' })"
  >
    <div class="field">
      <div
        v-for="(row, rowIndex) in field"
        :key="rowIndex"
        class="row"
      >
        <div
          v-for="(cell, cellIndex) in row"
          :key="`${rowIndex}_${cellIndex}`"
          :style="{ backgroundColor: cell }"
          class="cell"
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

export default {
  name: 'Snake',

  data() {
    return {
      field: [[]],
      fieldDefault: [[]],
      fieldSize,

      actors: {
        human: {
          name: 'human',
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
        ai: {
          name: 'ai',
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
      actorsDefault: {},

      // todo переключение режимов (mode), чтобы играть против МЛ вручную и потом возобновить обучение.
      mode: 'gaming', // training | gaming
    };
  },

  mounted() {
    this.initialField();
    this.initialActors();
    this.addApple();

    this.autoStep();
  },

  methods: {
    // Игровой алгоритм.
    initialField() {
      this.$refs.snake.style.setProperty('--rows', String(fieldSize));
      this.$refs.snake.style.setProperty('--columns', String(fieldSize));

      const field = Array(fieldSize);

      for (let y = 0; y < fieldSize; y += 1) {
        field[y] = Array(fieldSize);

        for (let x = 0; x < fieldSize; x += 1) {
          const isBarrier = y === 0 || y === fieldSize - 1 || x === 0 || x === fieldSize - 1;
          field[y][x] = isBarrier ? barrierColor : basicColor;
        }
      }

      this.field = field;
      this.fieldDefault = cloneDeep(this.field);
    },

    initialActors() {
      Object.values(this.actors).forEach(this.setupModel);
      this.actorsDefault = cloneDeep(this.actors);

      Object.values(this.actors).forEach((actor) => {
        actor.cells.forEach(({ position: { x, y } }, cellIndex) => {
          this.field[y][x] = cellIndex === 0 ? actor.colorHead : actor.colorTail;
        });

        actor.rewards = actor.rewards.map(() => basicReward);
      });
    },

    addApple() {
      const y = Math.round(Math.random() * (fieldSize - 1));
      const x = Math.round(Math.random() * (fieldSize - 1));

      if (this.field[y][x] === basicColor) {
        this.field[y][x] = appleColor;
      } else {
        this.addApple();
      }
    },

    handleKeys({ name, side }) {
      if (this.mode === 'gaming') {
        this.actors[name].side = side;
      }
    },

    async autoStep() {
      await Promise.all(Object.values(this.actors).map((actor) => (async () => {
        if (this.mode === 'gaming' && actor.name === 'human') {
          // pass
        } else {
          this.estimationSides(actor);

          // 0 - stepTop, 1 - stepRight, 2 - stepBottom, 3 - stepLeft.
          const sideIndex = await this.modelPredict(actor);
          actor.side = sides[sideIndex];
        }

        const { name, side } = actor;
        this.step({ name, side });
      })()));

      if (this.mode === 'training') {
        nextFrameId = requestAnimationFrame(this.autoStep);
      } else if (this.mode === 'gaming') {
        nextFrameId = setTimeout(this.autoStep, autoMovementDelay);
      }
    },

    step({ name, side }) {
      const actor = this.actors[name];

      this.clearTail(actor);
      this.stepTail(actor);
      this.stepHead({ actor, side });
    },

    clearTail({ cells }) {
      const { position: { x, y } } = cells[cells.length - 1];
      this.field[y][x] = basicColor;
    },

    stepTail(actor) {
      for (let i = actor.cells.length - 1; i > 0; i -= 1) {
        const cell = actor.cells[i];
        cell.position = actor.cells[i - 1].position;

        const { position: { x, y } } = cell;
        this.field[y][x] = actor.colorTail;
      }
    },

    stepHead({ actor, side }) {
      const [cell] = actor.cells;
      const { position: { x, y } } = cell;

      this[side]({ cell, x, y });

      this.nextCell(actor);
    },

    stepTop({ cell, x, y }) {
      cell.position = { x, y: y - 1 };
    },

    stepRight({ cell, x, y }) {
      cell.position = { x: x + 1, y };
    },

    stepBottom({ cell, x, y }) {
      cell.position = { x, y: y + 1 };
    },

    stepLeft({ cell, x, y }) {
      cell.position = { x: x - 1, y };
    },

    nextCell(actor) {
      const [{ position: { x, y } }] = actor.cells;
      const nextColor = this.field[y][x];

      if (colors.includes(nextColor)) {
        this.gameOver(actor);
      } else {
        this.field[y].splice(x, 1, actor.colorHead);

        if (nextColor === appleColor) {
          this.growth({ actor, x, y });
          this.addApple();
        }
      }
    },

    growth({ actor, x, y }) {
      actor.cells.push({
        id: nanoid(),
        position: { x, y },
      });
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
      console.log(actor);
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

  .row {
    display: grid;
    grid-template-columns: repeat(var(--columns), var(--size));

    .cell {
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 12px;
      color: #555;
    }
  }
}
</style>
