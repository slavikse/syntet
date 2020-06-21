<template>
  <div
    ref="snake"
    class="Snake"
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

    <div class="actors">
      <div
        v-for="actor in Object.values(actors)"
        :key="actor.name"
        class="actor"
      >
        <div
          :style="{ color: actor.colorHead }"
          class="name"
        >
          {{ actor.name }}:
        </div>

        <div
          v-if="stats[actor.name]"
          :style="{ color: actor.colorHead }"
          class="stats"
        >
          <div class="stat">
            <div class="title">
              Яблок:
            </div>

            <div>
              {{ stats[actor.name].maxApples }}
            </div>
          </div>

          <div class="stat">
            <div class="title">
              Побед:
            </div>

            <div>
              {{ stats[actor.name].victories }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="message">
      Игра против AI начнётся по нажатию: WASD
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';
import { nanoid } from 'nanoid';
import cloneDeep from 'clone-deep';

const fieldSize = 40;

const barrierColor = '#111';
const basicColor = '#222';
const appleColor = 'green';

const actorsColors = [
  // human
  'rgba(201, 52, 65, 1.0)',
  'rgba(201, 52, 65, 0.5)',

  // ai
  'rgba(34, 95, 228, 1.0)',
  'rgba(34, 95, 228, 0.5)',
];

const blocksColors = [
  ...actorsColors,
  barrierColor,
];

const keysWASD = {
  KeyW: 'stepTop',
  KeyD: 'stepRight',
  KeyS: 'stepBottom',
  KeyA: 'stepLeft',
};

const sides = {
  0: 'stepTop',
  1: 'stepRight',
  2: 'stepBottom',
  3: 'stepLeft',
};

let nextFrameId = -1;

const basicReward = 0.1;
// const barrierReward = -1;
// const appleReward = 1;

const numberSides = 4;
const autoMovementDelay = 150;

const isDev = true;

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

          colorHead: actorsColors[0],
          colorTail: actorsColors[1],
          cells: [
            { id: nanoid(), position: { y: 5, x: 3 } },
            { id: nanoid(), position: { y: 4, x: 3 } },
            { id: nanoid(), position: { y: 3, x: 3 } },
          ],

          model: tf.sequential(),
          training: { inputs: [], labels: [] },
          rewards: Array(numberSides).fill(basicReward),
        },
        ai: {
          name: 'ai',
          side: 'stepTop',

          colorHead: actorsColors[2],
          colorTail: actorsColors[3],
          cells: [
            { id: nanoid(), position: { y: fieldSize - 9, x: fieldSize - 4 } },
            { id: nanoid(), position: { y: fieldSize - 8, x: fieldSize - 4 } },
            { id: nanoid(), position: { y: fieldSize - 7, x: fieldSize - 4 } },
            { id: nanoid(), position: { y: fieldSize - 6, x: fieldSize - 4 } },
            { id: nanoid(), position: { y: fieldSize - 5, x: fieldSize - 4 } },
            { id: nanoid(), position: { y: fieldSize - 4, x: fieldSize - 4 } },
          ],

          model: tf.sequential(),
          training: { inputs: [], labels: [] },
          rewards: Array(numberSides).fill(basicReward),
        },
      },
      actorsDefault: {},

      stats: {},

      apples: [
        { y: -1, x: -1 },
        { y: -1, x: -1 },
      ],

      mode: isDev ? 'gaming' : 'training',
    };
  },

  mounted() {
    this.initialField();
    this.initialActors();
    this.initialStats();

    this.apples.forEach(this.addApple);
    this.autoStep();

    window.addEventListener('keydown', this.handleKeys);
  },

  destroyed() {
    window.removeEventListener('keydown', this.handleKeys);
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

      this.resetActors();
    },

    resetActors() {
      Object.values(this.actors).forEach((actor) => {
        actor.cells.forEach(({ position: { y, x } }, cellIndex) => {
          this.field[y][x] = cellIndex === 0 ? actor.colorHead : actor.colorTail;
        });

        actor.rewards = actor.rewards.map(() => basicReward);

        this.stats[actor.name] = {
          maxApples: 0,
        };
      });
    },

    initialStats() {
      Object.values(this.actors).forEach((actor) => {
        this.stats[actor.name] = {
          maxApples: 0,
          victories: 0,
        };
      });
    },

    addApple(coords) {
      const y = Math.round(Math.random() * (fieldSize - 1));
      const x = Math.round(Math.random() * (fieldSize - 1));

      if (this.field[y][x] === basicColor) {
        coords.y = y;
        coords.x = x;

        this.field[y][x] = appleColor;
      } else {
        this.addApple(coords);
      }
    },

    handleKeys({ code }) {
      const side = keysWASD[code];

      if (side) {
        this.mode = 'gaming';
        this.actors.human.side = side;
      }
    },

    async autoStep() {
      await Promise.all(Object.values(this.actors).map((actor) => (async () => {
        if (this.mode === 'gaming' && actor.name === 'human') {
          // pass
        } else {
          this.estimationSides(actor);

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
      const { position: { y, x } } = cells[cells.length - 1];
      this.field[y][x] = basicColor;
    },

    stepTail(actor) {
      for (let i = actor.cells.length - 1; i > 0; i -= 1) {
        const cell = actor.cells[i];
        cell.position = actor.cells[i - 1].position;

        const { position: { y, x } } = cell;
        this.field[y][x] = actor.colorTail;
      }
    },

    stepHead({ actor, side }) {
      const [cell] = actor.cells;
      const { position: { y, x } } = cell;

      this[side]({ cell, y, x });

      this.nextCell(actor);
    },

    stepTop({ cell, y, x }) {
      cell.position = { y: y - 1, x };
    },

    stepRight({ cell, y, x }) {
      cell.position = { y, x: x + 1 };
    },

    stepBottom({ cell, y, x }) {
      cell.position = { y: y + 1, x };
    },

    stepLeft({ cell, y, x }) {
      cell.position = { y, x: x - 1 };
    },

    nextCell(actor) {
      const [{ position: { y, x } }] = actor.cells;
      const nextColor = this.field[y][x];

      if (blocksColors.includes(nextColor)) {
        this.gameOver(actor);
      } else {
        this.field[y].splice(x, 1, actor.colorHead);

        if (nextColor === appleColor) {
          this.growth({ actor, y, x });

          const coords = this.apples.find((a) => `${a.y}_${a.x}` === `${y}_${x}`);
          this.addApple(coords);
        }
      }
    },

    growth({ actor, y, x }) {
      this.stats[actor.name].maxApples += 1;

      actor.cells.push({
        id: nanoid(),
        position: { y, x },
      });
    },

    gameOver(actor) {
      cancelAnimationFrame(nextFrameId);
      clearTimeout(nextFrameId);
      nextFrameId = -1;

      this.modelsFit({
        actor,
        callbackAtEndTraining: () => {
          this.field = cloneDeep(this.fieldDefault);
          this.actors = cloneDeep(this.actorsDefault);

          this.resetActors();
          this.apples.forEach(this.addApple);

          this.mode = isDev ? 'gaming' : 'training';
        },
      });
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
      actor.iii = 0;
      // actor.rewards
    },

    searchApples() {},

    /**
     * 0 - stepTop, 1 - stepRight, 2 - stepBottom, 3 - stepLeft.
     * @param actor
     * @returns {Promise<Number>}
     */
    async modelPredict(actor) {
      // todo
      const predictions = await actor.model.predict(tf.tensor2d([actor.rewards])).data();
      return predictions.indexOf(Math.max(...predictions));
    },

    // todo алгоритм оценки текущего положения и куда лучше сходить, после чего, ML выберет ход.
    // actor.rewards[nextColor] = barrierReward;
    // actor.rewards[nextColor] = appleReward;

    // todo обучение моделей. fit
    // actor,
    modelsFit({ callbackAtEndTraining }) {
      // console.log(actor);
      callbackAtEndTraining();
    },
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
  --size: 25px;

  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100vh;
  user-select: none;
  outline: none;

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

  .actors {
    margin-top: 20px;

    .actor {
      margin-bottom: 10px;
      display: flex;
      justify-content: space-between;

      .name {
        padding-right: 10px;
        width: 100%;
        text-align: end;
        text-transform: uppercase;
      }

      .stats {
        font-weight: bold;

        .stat {
          display: flex;
          justify-content: space-between;
          min-width: 70px;

          .title {
            padding-right: 4px;
          }
        }
      }
    }
  }

  .message {
    margin-top: 20px;
    text-align: center;
    color: gray;
  }
}
</style>
