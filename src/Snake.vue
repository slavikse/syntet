<template>
  <div class="Snake">
    <div class="text-container">
      <div class="message">
        Ручное управление WASD
      </div>

      <div class="steps-count">
        Количество оставшихся ходов: {{ maximumStepsCount - stepsCount }}
      </div>

      <div class="timer">
        Время обучения: {{ timer }} секунд (~{{ Math.round(timer / 60) }} минут)
      </div>

      <div class="lives">
        Сыграно жизней: {{ lives }}
      </div>

      <div class="actors-container">
        <div class="title">
          Собрано яблок за жизнь
        </div>

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
        >
          <!-- {{ rowIndex }} {{ cellIndex }}-->
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';
import { nanoid } from 'nanoid';
import cloneDeep from 'clone-deep';

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

const isDevelopment = false;
const autoMovementDelay = 50;

const fieldSize = 60;
const stepsCountMultiplier = 2.5;
const applesCount = 1;

const hiddenLayers = 1;
const units = 2000;
const epochs = 1;

const terribleReward = -0.9;
const badReward = -0.9;
const basicReward = 0.1;
const goodReward = 0.9;
const bestReward = 0.9;

const decreaseMultiplier = 0.9;
const increaseMultiplier = 1.1;

let isFitting = false;
let nextFrameId = -1;

const startPositions = {
  center: [
    { id: nanoid(), position: { y: 9, x: 7 } },
    { id: nanoid(), position: { y: 9, x: 8 } },
    { id: nanoid(), position: { y: 8, x: 8 } },
    { id: nanoid(), position: { y: 7, x: 8 } },
    { id: nanoid(), position: { y: 7, x: 7 } },
  ],
  topLeft: [
    { id: nanoid(), position: { y: 7, x: 3 } },
    { id: nanoid(), position: { y: 6, x: 3 } },
    { id: nanoid(), position: { y: 5, x: 3 } },
    { id: nanoid(), position: { y: 4, x: 3 } },
    { id: nanoid(), position: { y: 3, x: 3 } },
  ],
  topRight: [
    { id: nanoid(), position: { y: 3, x: fieldSize - 8 } },
    { id: nanoid(), position: { y: 3, x: fieldSize - 7 } },
    { id: nanoid(), position: { y: 3, x: fieldSize - 6 } },
    { id: nanoid(), position: { y: 3, x: fieldSize - 5 } },
    { id: nanoid(), position: { y: 3, x: fieldSize - 4 } },
  ],
  bottomRight: [
    { id: nanoid(), position: { y: fieldSize - 8, x: fieldSize - 4 } },
    { id: nanoid(), position: { y: fieldSize - 7, x: fieldSize - 4 } },
    { id: nanoid(), position: { y: fieldSize - 6, x: fieldSize - 4 } },
    { id: nanoid(), position: { y: fieldSize - 5, x: fieldSize - 4 } },
    { id: nanoid(), position: { y: fieldSize - 4, x: fieldSize - 4 } },
  ],
  bottomLeft: [
    { id: nanoid(), position: { y: fieldSize - 4, x: 7 } },
    { id: nanoid(), position: { y: fieldSize - 4, x: 6 } },
    { id: nanoid(), position: { y: fieldSize - 4, x: 5 } },
    { id: nanoid(), position: { y: fieldSize - 4, x: 4 } },
    { id: nanoid(), position: { y: fieldSize - 4, x: 3 } },
  ],
};

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
          cells: cloneDeep(startPositions.topLeft),

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
        //   cells: cloneDeep(startPositions.bottomRight),
        //
        //   model: tf.sequential(),
        //   training: { inputs: [], labels: [] },
        //   rewards: Array(numberSides).fill(basicReward),
        // },
      },
      actorsDefault: {},

      stats: {}, // Инициализируется в initialStats на основе actors.
      stepsCount: 0,
      maximumStepsCount: fieldSize * stepsCountMultiplier,
      timer: 0,
      lives: 0,
      everyLives: 300,

      apples: [],

      mode: isDevelopment ? 'gaming' : 'training',
      isRunning: true,
    };
  },

  mounted() {
    const version = 2;
    console.log(version);

    this.incrementTimer();

    this.initialField();
    this.initialApples();
    this.initialActors();
    this.initialStats();

    // this.chooseActorsPosition();

    this.autoStep();
    window.addEventListener('keydown', this.handleKeys);
  },

  destroyed() {
    window.removeEventListener('keydown', this.handleKeys);
  },

  methods: {
    incrementTimer() {
      setTimeout(this.incrementTimer, 1000);
      this.timer += 1;
    },

    initialField() {
      const field = Array(fieldSize);

      for (let y = 0; y < fieldSize; y += 1) {
        field[y] = Array(fieldSize);

        for (let x = 0; x < fieldSize; x += 1) {
          const isBarrier = y <= 0 || y >= fieldSize - 1 || x <= 0 || x >= fieldSize - 1;
          field[y][x] = isBarrier ? barrierColor : basicColor;
        }
      }

      // todo статичные преграды
      // field[10][3] = barrierColor;
      // field[10][4] = barrierColor;
      // field[10][5] = barrierColor;
      // field[10][6] = barrierColor;
      // field[10][7] = barrierColor;
      // field[10][8] = barrierColor;
      // field[10][9] = barrierColor;
      // field[10][10] = barrierColor;
      // field[10][11] = barrierColor;

      this.field = field;
      this.fieldDefault = cloneDeep(this.field);
    },

    initialApples() {
      for (let i = 0; i < applesCount; i += 1) {
        this.apples.push({ y: -1, x: -1 });
      }

      this.apples.forEach(this.addApple);
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

    chooseActorsPosition() {
      const positions = Object.keys(startPositions);
      const position = positions[Math.round((positions.length - 1) * Math.random())];

      Object.values(this.actors).forEach((actor) => {
        actor.cells = cloneDeep(startPositions[position]);
      });
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

    step(actor) {
      this.clearTail(actor);
      this.stepTail(actor);
      this.stepHead(actor);
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

    stepHead(actor) {
      const [cellHead] = actor.cells;
      const { y, x } = this[actor.side](cellHead.position);

      this.nextCell({ actor, cellHead, y, x });
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

    nextCell({ actor, cellHead, y, x }) {
      const nextColor = this.field[y][x];

      if (barriersColors.includes(nextColor)) {
        this.preserveExperience({ type: 'decrease', actor });
        this.gameOver();
      } else if (nextColor === appleColor) {
        this.preserveExperience({ type: 'increase', actor });
        this.growth({ actor, y, x });
        this.applyNextCell({ actor, cellHead, y, x });

        const coords = this.apples.find((a) => `${a.y}_${a.x}` === `${y}_${x}`);
        this.addApple(coords);

        this.appleFit();
      } else {
        this.preserveExperience({ type: 'pass', actor });
        this.applyNextCell({ actor, cellHead, y, x });
      }
    },

    applyNextCell({ actor, cellHead, y, x }) {
      cellHead.position = { y, x };
      this.field[y][x] = actor.colorHead;
    },

    growth({ actor, y, x }) {
      this.stats[actor.name].apples += 1;

      if (this.stats[actor.name].apples > this.stats[actor.name].maxApples) {
        this.stats[actor.name].maxApples = this.stats[actor.name].apples;
      }

      this.stepsCount = 0;

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

        // this.chooseActorsPosition();

        this.resetActors();
        this.resetStats();

        this.apples.forEach(this.addApple);

        this.mode = isDevelopment ? 'gaming' : 'training';
        this.isRunning = true;
      });
    },

    // ----------------------------------------- Алгоритм ML -------------------------------------------------

    setupModel({ model }) {
      model.add(tf.layers.dense({
        inputShape: [
          // +4 - Занятость ближних ячеек.
          // +4 - Направления яблока.
          // +1 - Расстояние до ближнего яблока.
          // +1 - Количество ходов.
          numberSides + numberSides + 1 + 1,
        ],
        activation: 'relu',
        units,
      }));

      for (let i = 0; i < hiddenLayers; i += 1) {
        model.add(tf.layers.dense({
          activation: 'relu',
          units,
        }));
      }

      model.add(tf.layers.dense({
        activation: 'sigmoid',
        units: numberSides,
      }));

      model.compile({
        optimizer: 'adam',
        loss: 'meanSquaredError',
      });
    },

    async modelsPredicts() {
      await Promise.all(Object.values(this.actors).map((actor) => (async () => {
        if (this.mode === 'gaming' && actor.name === 'human') {
          await this.modelPredict(actor);
        } else {
          const indexSide = await this.modelPredict(actor);
          actor.side = indexSides[indexSide];
        }

        this.step(actor);
      })()));

      // await new Promise((resolve) => {
      //   setTimeout(resolve, autoMovementDelay);
      // });

      this.stepsCount += 1;

      if (this.stepsCount === this.maximumStepsCount) {
        this.gameOver();
      }
    },

    async modelPredict(actor) {
      const dataInputs = this.assessment(actor);
      this.whichSidesOfApples(actor);

      const inputs = dataInputs.concat(actor.rewards);
      const sides = await actor.model.predict(tf.tensor2d([inputs])).data();

      // if (this.lives % this.everyLives === 0) {
      //   console.log('modelPredict', sides);
      // }

      return sides.indexOf(Math.max(...sides));
    },

    assessment(actor) {
      const [{ position: actorHead }] = actor.cells;
      const inputs = [];

      Object.keys(sidesIndex).forEach((side) => {
        const { y: nextY, x: nextX } = this[side]({ y: actorHead.y, x: actorHead.x });
        const nextColor = this.field[nextY][nextX];

        if (barriersColors.includes(nextColor)) {
          inputs.push(terribleReward);
        } else if (nextColor === appleColor) {
          inputs.push(bestReward);
        } else {
          inputs.push(goodReward);
        }
      });

      inputs.push(this.getDippedAppleReward(actorHead));
      inputs.push(this.estimateNumberMoves());

      return inputs;
    },

    getDippedAppleReward(actorHead) {
      let appleReward = 0;

      this.apples.forEach((apple) => {
        const distance = this.distanceToApple({ apple, actorHead });
        const reward = (fieldSize - (distance + 1)) / fieldSize;

        if (reward > appleReward) {
          appleReward = reward;
        }
      });

      return appleReward;
    },

    distanceToApple({ apple, actorHead }) {
      const x = (apple.x - actorHead.x) ** 2;
      const y = (apple.y - actorHead.y) ** 2;

      return Math.sqrt(x + y);
    },

    estimateNumberMoves() {
      const fieldSizeBestReward = fieldSize * 0.5;

      if (((fieldSizeBestReward - this.stepsCount) / fieldSizeBestReward) > 0) {
        return bestReward;
      }

      if (((fieldSize - this.stepsCount) / fieldSize) > 0) {
        return goodReward;
      }

      const fieldSizeBasicReward = fieldSize * 1.5;

      if (((fieldSizeBasicReward - this.stepsCount) / fieldSizeBasicReward) > 0) {
        return basicReward;
      }

      return badReward;
    },

    preserveExperience({ type, actor }) {
      const dataInputs = this.assessment(actor);
      this.whichSidesOfApples(actor);

      const inputs = dataInputs.concat(actor.rewards);

      actor.training.inputs.push(inputs);
      actor.training.labels.push(actor.rewards);

      if (type === 'decrease') {
        actor.training.inputs = actor.training.inputs
          .map((trainInputs) => trainInputs.map((input) => input * decreaseMultiplier));

        actor.training.labels = actor.training.labels
          .map((trainLabels) => trainLabels.map((label) => label * decreaseMultiplier));
      } else if (type === 'increase') {
        actor.training.inputs = actor.training.inputs
          .map((trainInputs) => trainInputs.map((input) => input * increaseMultiplier));

        actor.training.labels = actor.training.labels
          .map((trainLabels) => trainLabels.map((label) => label * increaseMultiplier));
      }

      // if (isDevelopment) {
      //   console.log('---');
      //   actor.training.inputs.forEach((input) => console.log(input));
      //   actor.training.labels.forEach((label) => console.log(label));
      //   console.log(actor.rewards);
      // }

      this.resetRewards(actor);
    },

    whichSidesOfApples(actor) {
      const [{ position: actorHead }] = actor.cells;

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
      actor.rewards[sidesIndex.stepTop] = bestReward;
      actor.rewards[sidesIndex.stepBottom] = terribleReward;
    },

    appleBottom(actor) {
      actor.rewards[sidesIndex.stepBottom] = bestReward;
      actor.rewards[sidesIndex.stepTop] = terribleReward;
    },

    appleOnAxisY({ apple, actor, actorHead }) {
      if (apple.x > actorHead.x) {
        this.appleRight(actor);
      } else if (apple.x < actorHead.x) {
        this.appleLeft(actor);
      }
    },

    appleRight(actor) {
      actor.rewards[sidesIndex.stepRight] = bestReward;
      actor.rewards[sidesIndex.stepLeft] = terribleReward;
    },

    appleLeft(actor) {
      actor.rewards[sidesIndex.stepLeft] = bestReward;
      actor.rewards[sidesIndex.stepRight] = terribleReward;
    },

    appleBelowAxisY({ apple, actor, actorHead }) {
      if (apple.x < actorHead.x) {
        this.appleTopLeft(actor);
      } else if (apple.x > actorHead.x) {
        this.appleTopRight(actor);
      }
    },

    appleTopLeft(actor) {
      actor.rewards[sidesIndex.stepTop] = goodReward;
      actor.rewards[sidesIndex.stepLeft] = goodReward;

      actor.rewards[sidesIndex.stepRight] = badReward;
      actor.rewards[sidesIndex.stepBottom] = badReward;
    },

    appleTopRight(actor) {
      actor.rewards[sidesIndex.stepTop] = goodReward;
      actor.rewards[sidesIndex.stepRight] = goodReward;

      actor.rewards[sidesIndex.stepBottom] = badReward;
      actor.rewards[sidesIndex.stepLeft] = badReward;
    },

    appleAboveAxisY({ apple, actor, actorHead }) {
      if (apple.x > actorHead.x) {
        this.appleBottomRight(actor);
      } else if (apple.x < actorHead.x) {
        this.appleBottomLeft(actor);
      }
    },

    appleBottomRight(actor) {
      actor.rewards[sidesIndex.stepRight] = goodReward;
      actor.rewards[sidesIndex.stepBottom] = goodReward;

      actor.rewards[sidesIndex.stepTop] = badReward;
      actor.rewards[sidesIndex.stepLeft] = badReward;
    },

    appleBottomLeft(actor) {
      actor.rewards[sidesIndex.stepBottom] = goodReward;
      actor.rewards[sidesIndex.stepLeft] = goodReward;

      actor.rewards[sidesIndex.stepTop] = badReward;
      actor.rewards[sidesIndex.stepRight] = badReward;
    },

    appleFit() {
      this.isRunning = false;

      cancelAnimationFrame(nextFrameId);
      clearTimeout(nextFrameId);
      nextFrameId = -1;

      this.modelFit(() => {
        this.mode = isDevelopment ? 'gaming' : 'training';
        this.isRunning = true;
      });
    },

    modelFit(callbackAtEndTraining) {
      // Обучение происходит для всех, поэтому требуется только одно выполнение.
      if (isFitting) {
        return;
      }

      isFitting = true;
      this.lives += 1;

      Promise.all(Object.values(this.actors).map(async (actor) => {
        if (actor.training.labels.length > 0) {
          await actor.model.fit(
            tf.tensor2d(actor.training.inputs),
            tf.tensor2d(actor.training.labels),
            { epochs },
          );

          actor.training.inputs = [];
          actor.training.labels = [];
        }
      })).then(async () => {
        // await new Promise((resolve) => {
        //   setTimeout(resolve, autoMovementDelay);
        // });

        isFitting = false;
        callbackAtEndTraining();
      });
    },
  },
};
</script>

<style
  lang="scss"
  scoped
>
.Snake {
  --size: 12px;

  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  user-select: none;
  outline: none;

  .text-container {
    width: 300px;
    text-align: center;

    .message {
      margin-top: 10px;
      text-align: center;
      color: gray;
    }

    .steps-count {
      text-align: center;
      color: dimgray;
    }

    .timer {
      font-size: 14px;
      color: dimgray;
    }

    .lives {
      font-size: 14px;
      color: dimgray;
    }

    .actors-container {
      margin-top: 20px;

      .title {
        font-size: 16px;
        color: gray;
      }

      .actor {
        display: flex;
        justify-content: center;

        .name {
          padding-right: 10px;
          text-transform: uppercase;
        }

        .stats {
          font-weight: bold;
          min-width: 30px;
        }
      }
    }
  }

  .field {
    margin-left: 20px;

    .row {
      display: flex;

      .cell {
        display: flex;
        justify-content: center;
        align-items: center;
        width: var(--size);
        height: var(--size);
        font-size: 10px;
        color: #777;
      }
    }
  }
}
</style>
