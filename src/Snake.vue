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

    <div class="message">
      Игра против AI начнётся по нажатию: WASD
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
          {{ stats[actor.name].maxApples }}
        </div>
      </div>
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

const barriersColors = [
  ...actorsColors,
  barrierColor,
];

const keysWASD = {
  KeyW: 'stepTop',
  KeyD: 'stepRight',
  KeyS: 'stepBottom',
  KeyA: 'stepLeft',
};

const indexSides = {
  0: 'stepTop',
  1: 'stepRight',
  2: 'stepBottom',
  3: 'stepLeft',
};

const sidesIndex = {
  stepTop: 0,
  stepRight: 1,
  stepBottom: 2,
  stepLeft: 3,
};

const numberSides = Object.keys(indexSides).length;

const autoMovementDelay = 150;
const maximumStepsCount = fieldSize * 3;
const isDevelopment = false;

let nextFrameId = -1;

// --- ML ---

// Награды.
const barrierReward = -1.0;
const basicReward = 0.1;
const freeReward = 0.3;
const appleReward = 1.0;

// todo добавить статичные преграды

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
            { id: nanoid(), position: { y: 6, x: 3 } },
            { id: nanoid(), position: { y: 5, x: 3 } },
            { id: nanoid(), position: { y: 4, x: 3 } },
            { id: nanoid(), position: { y: 3, x: 3 } },
            { id: nanoid(), position: { y: 2, x: 3 } },
          ],

          model: tf.sequential(),
          training: { inputs: [], labels: [] },
          rewards: Array(numberSides).fill(basicReward),
        },
        // ai: {
        //   name: 'ai',
        //   side: 'stepTop',
        //
        //   colorHead: actorsColors[2],
        //   colorTail: actorsColors[3],
        //   cells: [
        //     { id: nanoid(), position: { y: fieldSize - 9, x: fieldSize - 4 } },
        //     { id: nanoid(), position: { y: fieldSize - 8, x: fieldSize - 4 } },
        //     { id: nanoid(), position: { y: fieldSize - 7, x: fieldSize - 4 } },
        //     { id: nanoid(), position: { y: fieldSize - 6, x: fieldSize - 4 } },
        //     { id: nanoid(), position: { y: fieldSize - 5, x: fieldSize - 4 } },
        //   ],
        //
        //   model: tf.sequential(),
        //   training: { inputs: [], labels: [] },
        //   rewards: Array(numberSides).fill(basicReward),
        // },
      },
      actorsDefault: {},

      stats: {}, // Инициализируется в initialStats на основе actors.
      stepsCount: 0,

      // todo для сбора двух и более яблок, нужен алгоритм ближайшего яблока + для обучения
      apples: [
        { y: -1, x: -1 },
        // { y: -1, x: -1 },
      ],

      mode: isDevelopment ? 'gaming' : 'training',
      isRunning: true,
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

        this.resetRewards(actor);
      });
    },

    resetRewards(actor) {
      actor.rewards = actor.rewards.map(() => basicReward);
    },

    initialStats() {
      Object.values(this.actors).forEach((actor) => {
        this.stats[actor.name] = {
          apples: 0,
          maxApples: 0,
        };
      });
    },

    resetStats() {
      Object.values(this.actors).forEach((actor) => {
        this.stats[actor.name].apples = 0;
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
      if (this.isRunning) {
        await this.modelsPredicts();
      }

      if (this.mode === 'training') {
        nextFrameId = requestAnimationFrame(this.autoStep);
      } else if (this.mode === 'gaming') {
        nextFrameId = setTimeout(this.autoStep, autoMovementDelay);
      }
    },

    async modelsPredicts() {
      await Promise.all(Object.values(this.actors).map((actor) => (async () => {
        if (this.mode === 'gaming' && actor.name === 'human') {
          // pass
          // this.estimationSides(actor);
        } else {
          this.estimationSides(actor);

          const indexSide = await this.modelPredict(actor);
          actor.side = indexSides[indexSide];
        }

        const { name, side } = actor;
        this.step({ name, side });

        // todo
        this.preserveExperience(actor);
      })()));

      this.stepsCount += 1;

      if (this.stepsCount === maximumStepsCount) {
        this.gameOver();
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

      cell.position = this[side]({ y, x });
      this.nextCell(actor);
    },

    stepTop({ y, x }) {
      return { y: y - 1, x };
    },

    stepRight({ y, x }) {
      return { y, x: x + 1 };
    },

    stepBottom({ y, x }) {
      return { y: y + 1, x };
    },

    stepLeft({ y, x }) {
      return { y, x: x - 1 };
    },

    nextCell(actor) {
      const [{ position: { y, x } }] = actor.cells;
      const nextColor = this.field[y][x];

      this.estimationNextCell(actor);

      if (barriersColors.includes(nextColor)) {
        this.preserveExperience(actor);
        this.gameOver();
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
      this.stats[actor.name].apples += 1;

      if (this.stats[actor.name].apples > this.stats[actor.name].maxApples) {
        this.stats[actor.name].maxApples = this.stats[actor.name].apples;
      }

      actor.cells.push({
        id: nanoid(),
        position: { y, x },
      });
    },

    gameOver() {
      this.isRunning = false;
      this.stepsCount = 0;

      cancelAnimationFrame(nextFrameId);
      clearTimeout(nextFrameId);
      nextFrameId = -1;

      this.modelFit(() => {
        this.field = cloneDeep(this.fieldDefault);
        this.actors = cloneDeep(this.actorsDefault);

        this.resetActors();
        this.resetStats();

        this.apples.forEach(this.addApple);

        this.mode = isDevelopment ? 'gaming' : 'training';
        this.isRunning = true;
      });
    },

    // ------------------------- Алгоритм ML -------------------------------------------------

    setupModel({ model }) {
      model.add(tf.layers.dense({
        inputShape: [fieldSize ** 2],
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

    // todo сканер для преград. расстояние? или следующая ячейка
    // todo расстояние до ближайшего яблока
    //  доля от расстояния до приближения к яблоку
    //  то яблоко, что дальше, имеет меньшую ценность
    // todo врага так же разметить как -1 (стена)
    estimationSides(actor) {
      const [{ position: actorHead }] = actor.cells;
      this.whichSidesOfApples({ actor, actorHead });
      this.assessmentNearbyObstacles({ actor, actorHead });
    },

    whichSidesOfApples({ actor, actorHead }) {
      this.apples.forEach((apple) => {
        if (apple.x === actorHead.x) {
          this.appleOnAxisX({ apple, actor, actorHead });
        } else if (apple.y === actorHead.y) {
          this.appleOnAxisY({ apple, actor, actorHead });
        } else if (apple.y < actorHead.y) {
          this.appleBelowAxisY({ apple, actor, actorHead });
        } else if (apple.y > actorHead.y) {
          this.appleAboveAxisY({ apple, actor, actorHead });
        }
      });
    },

    appleOnAxisX({ apple, actor, actorHead }) {
      if (apple.y < actorHead.y) {
        this.appleTop(actor);
      } else if (apple.y > actorHead.y) {
        this.appleBottom(actor);
      }
    },

    appleTop(actor) {
      actor.rewards[sidesIndex.stepTop] += appleReward;
      actor.rewards[sidesIndex.stepBottom] += barrierReward;
    },

    appleBottom(actor) {
      actor.rewards[sidesIndex.stepBottom] += appleReward;
      actor.rewards[sidesIndex.stepTop] += barrierReward;
    },

    appleOnAxisY({ apple, actor, actorHead }) {
      if (apple.x > actorHead.x) {
        this.appleRight(actor);
      } else if (apple.x < actorHead.x) {
        this.appleLeft(actor);
      }
    },

    appleRight(actor) {
      actor.rewards[sidesIndex.stepRight] += appleReward;
      actor.rewards[sidesIndex.stepLeft] += barrierReward;
    },

    appleLeft(actor) {
      actor.rewards[sidesIndex.stepLeft] += appleReward;
      actor.rewards[sidesIndex.stepRight] += barrierReward;
    },

    appleBelowAxisY({ apple, actor, actorHead }) {
      if (apple.x < actorHead.x) {
        this.appleTopLeft(actor);
      } else if (apple.x > actorHead.x) {
        this.appleTopRight(actor);
      }
    },

    appleTopLeft(actor) {
      actor.rewards[sidesIndex.stepTop] += appleReward;
      actor.rewards[sidesIndex.stepLeft] += appleReward;

      actor.rewards[sidesIndex.stepRight] += basicReward;
      actor.rewards[sidesIndex.stepBottom] += basicReward;
    },

    appleTopRight(actor) {
      actor.rewards[sidesIndex.stepTop] += appleReward;
      actor.rewards[sidesIndex.stepRight] += appleReward;

      actor.rewards[sidesIndex.stepBottom] += basicReward;
      actor.rewards[sidesIndex.stepLeft] += basicReward;
    },

    appleAboveAxisY({ apple, actor, actorHead }) {
      if (apple.x > actorHead.x) {
        this.appleBottomRight(actor);
      } else if (apple.x < actorHead.x) {
        this.appleBottomLeft(actor);
      }
    },

    appleBottomRight(actor) {
      actor.rewards[sidesIndex.stepRight] += appleReward;
      actor.rewards[sidesIndex.stepBottom] += appleReward;

      actor.rewards[sidesIndex.stepTop] += basicReward;
      actor.rewards[sidesIndex.stepLeft] += basicReward;
    },

    appleBottomLeft(actor) {
      actor.rewards[sidesIndex.stepBottom] += appleReward;
      actor.rewards[sidesIndex.stepLeft] += appleReward;

      actor.rewards[sidesIndex.stepTop] += basicReward;
      actor.rewards[sidesIndex.stepRight] += basicReward;
    },

    assessmentNearbyObstacles({ actor, actorHead: { y, x } }) {
      ['stepTop', 'stepRight', 'stepBottom', 'stepLeft'].forEach((side, sideIndex) => {
        const { y: nextY, x: nextX } = this[side]({ y, x });
        const nextColor = this.field[nextY][nextX];

        actor.rewards[sideIndex] += barriersColors.includes(nextColor) ? barrierReward : basicReward;
      });
    },

    async modelPredict(actor) {
      const inputs = this.fieldEstimation();
      const sides = await actor.model.predict(tf.tensor2d([inputs])).data();

      return sides.indexOf(Math.max(...sides));
    },

    fieldEstimation() {
      const inputs = [];

      this.field.forEach((row) => {
        row.forEach((cell) => {
          if (barriersColors.includes(cell)) {
            inputs.push(barrierReward);
          } else if (cell === appleColor) {
            inputs.push(appleReward);
          } else {
            inputs.push(freeReward);
          }
        });
      });

      return inputs;
    },

    estimationNextCell(actor) {
      actor.rewards.forEach((_, rewardIndex) => {
        if (sidesIndex[actor.side] === rewardIndex) {
          actor.rewards[rewardIndex] += barrierReward;
        } else {
          actor.rewards[rewardIndex] += freeReward;
        }
      });
    },

    preserveExperience(actor) {
      const inputs = this.fieldEstimation();

      actor.training.inputs.push(inputs);
      actor.training.labels.push(actor.rewards);
    },

    modelFit(callbackAtEndTraining) {
      Promise.all(Object.values(this.actors).map(async (actor) => {
        if (actor.training.labels.length > 0) {
          await actor.model.fit(
            tf.tensor2d(actor.training.inputs),
            tf.tensor2d(actor.training.labels),
          );

          actor.training.inputs = [];
          actor.training.labels = [];

          this.resetRewards(actor);
        }
      })).then(callbackAtEndTraining);
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

  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
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

  .message {
    margin-top: 10px;
    text-align: center;
    color: gray;
  }

  .actors {
    margin-top: 20px;

    .actor {
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
        min-width: 30px;
      }
    }
  }
}
</style>
