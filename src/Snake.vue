<template>
  <div class="Snake">
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

    <div class="message">
      Игра против AI начнётся по нажатию: WASD
    </div>

    <div class="steps-count">
      Количество оставшихся ходов: {{ maximumStepsCount - stepsCount }}
    </div>

    <div class="timer">
      Время обучения: {{ timer }} секунд (~{{ Math.round(timer / 60) }} минут)
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
const fieldSize = 30;
const autoMovementDelay = 500;

const terribleReward = -1.0;
const badReward = -1.0; // -0.4
const basicReward = 0.1;
const goodReward = 1.0; // 0.8
const bestReward = 5.0;
const excellentReward = 10.0; // 2.0
const epochs = 32;

let nextFrameId = -1;

// todo статичные преграды

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
            { id: nanoid(), position: { y: 7, x: 3 } },
            { id: nanoid(), position: { y: 6, x: 3 } },
            { id: nanoid(), position: { y: 5, x: 3 } },
            { id: nanoid(), position: { y: 4, x: 3 } },
            { id: nanoid(), position: { y: 3, x: 3 } },
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
        //     { id: nanoid(), position: { y: fieldSize - 6, x: fieldSize - 4 } },
        //     { id: nanoid(), position: { y: fieldSize - 5, x: fieldSize - 4 } },
        //     { id: nanoid(), position: { y: fieldSize - 4, x: fieldSize - 4 } },
        //     { id: nanoid(), position: { y: fieldSize - 3, x: fieldSize - 4 } },
        //     { id: nanoid(), position: { y: fieldSize - 2, x: fieldSize - 4 } },
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
      maximumStepsCount: fieldSize * 10,
      timer: 0,

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

    this.incrementTimer();

    window.addEventListener('keydown', this.handleKeys);
  },

  destroyed() {
    window.removeEventListener('keydown', this.handleKeys);
  },

  methods: {
    initialField() {
      const field = Array(fieldSize);

      for (let y = 0; y < fieldSize; y += 1) {
        field[y] = Array(fieldSize);

        for (let x = 0; x < fieldSize; x += 1) {
          const isBarrier = y <= 1 || y >= fieldSize - 2 || x <= 1 || x >= fieldSize - 2;
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

    incrementTimer() {
      setTimeout(this.incrementTimer, 1000);
      this.timer += 1;
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
        // nextFrameId = setTimeout(this.autoStep, autoMovementDelay);
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
        // this.changeExperienceReward({ type: 'decrease', actor });
        this.preserveExperience(actor);
        this.gameOver();
      } else {
        /* eslint-disable */
        if (nextColor === appleColor) {
          // this.changeExperienceReward({ type: 'increase', actor });
          this.preserveExperience(actor);
          this.growth({ actor, y, x });

          const coords = this.apples.find((a) => `${a.y}_${a.x}` === `${y}_${x}`);
          this.addApple(coords);
        } else {
          // this.preserveExperience(actor);
        }

        cellHead.position = { y, x };
        this.field[y][x] = actor.colorHead;
      }
    },

    growth({ actor, y, x }) {
      this.stats[actor.name].apples += 1;

      if (this.stats[actor.name].apples > this.stats[actor.name].maxApples) {
        this.stats[actor.name].maxApples = this.stats[actor.name].apples;
      }

      // todo индивидуальную? которая просто остановит игру для игрока, а другой будет играть?
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

        this.resetActors();
        this.resetStats();

        this.apples.forEach(this.addApple);

        this.mode = isDevelopment ? 'gaming' : 'training';
        this.isRunning = true;
      });
    },

    // ----------------------------------------- Алгоритм ML -------------------------------------------------

    // todo + близость яблока, преграды
    setupModel({ model }) {
      model.add(tf.layers.dense({
        // todo
        inputShape: [numberSides], // fieldSize ** 2
        activation: 'sigmoid',
        units: 1024,
      }));

      // model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 32,
      // }));
      //
      // model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 24,
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

    // todo сканер для далёких (ближайшая уже оценивается) преград? расстояние?
    // todo для двух и более яблок: расстояние до ближайшего яблока
    //  доля от расстояния до приближения к яблоку то яблоко, что дальше, имеет меньшую ценность
    // todo врага так же разметить как -1 (стена)
    async modelsPredicts() {
      await Promise.all(Object.values(this.actors).map((actor) => (async () => {
        const [{ position: actorHead }] = actor.cells;

        // todo оценивается предыдущая ячейка головы???
        this.whichSidesOfApples({ actor, actorHead });
        this.assessmentNearbyObstacles({ actor, actorHead });

        // console.log(actor.rewards);

        if (this.mode === 'gaming' && actor.name === 'human') {
          // pass
        } else {
          const indexSide = await this.modelPredict(actor);
          actor.side = indexSides[indexSide];
        }

        this.step(actor);
      })()));

      this.stepsCount += 1;

      if (this.stepsCount === this.maximumStepsCount) {
        this.gameOver();
      }
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

    assessmentNearbyObstacles({ actor, actorHead: { y, x } }) {
      Object.keys(sidesIndex).forEach((side, sideIndex) => {
        const { y: nextY, x: nextX } = this[side]({ y, x });
        const nextColor = this.field[nextY][nextX];

        if (barriersColors.includes(nextColor)) {
          actor.rewards[sideIndex] = terribleReward;
        }
      });
    },

    async modelPredict(actor) {
      // const inputs = this.fieldEstimation();
      const inputs = [];
      const [{ position: { y, x } }] = actor.cells;

      Object.keys(sidesIndex).forEach((side, sideIndex) => {
        const { y: nextY, x: nextX } = this[side]({ y, x });
        const nextColor = this.field[nextY][nextX];

        if (barriersColors.includes(nextColor)) {
          inputs[sideIndex] = terribleReward;
        } else {
          inputs[sideIndex] = goodReward;
        }
      });

      const sides = await actor.model.predict(tf.tensor2d([inputs])).data();
      return sides.indexOf(Math.max(...sides));
    },

    // todo сюда добавлять оценку интересных объектов или в rewards? или и туда и туда?
    // fieldEstimation() {
    //   const inputs = [];
    //
    //   this.field.forEach((row) => {
    //     row.forEach((cell) => {
    //       if (barriersColors.includes(cell)) {
    //         inputs.push(terribleReward);
    //       } else if (cell === appleColor) {
    //         inputs.push(bestReward);
    //       } else {
    //         inputs.push(goodReward);
    //       }
    //     });
    //   });
    //
    //   return inputs;
    // },

    preserveExperience(actor) {
      const inputs = [];
      const [{ position: { y, x } }] = actor.cells;

      Object.keys(sidesIndex).forEach((side, sideIndex) => {
        const { y: nextY, x: nextX } = this[side]({ y, x });
        const nextColor = this.field[nextY][nextX];

        if (barriersColors.includes(nextColor)) {
          inputs[sideIndex] = terribleReward;
        } else {
          inputs[sideIndex] = goodReward;
        }
      });

      actor.training.inputs.push(inputs);
      actor.training.labels.push(actor.rewards);
    },

    changeExperienceReward({ type, actor }) {
      if (type === 'decrease') {
        actor.rewards[sidesIndex[actor.side]] = terribleReward;
      } else if (type === 'increase') {
        actor.rewards[sidesIndex[actor.side]] = excellentReward;
      }
    },

    // todo если было собрано яблоко, то все ходы сделанные для сбора, получают +1, те, которые не меньше 0
    // те, которые привели в проигрышу занижаются.
    modelFit(callbackAtEndTraining) {
      Promise.all(Object.values(this.actors).map(async (actor) => {
        if (actor.training.labels.length > 0) {
          await actor.model.fit(
            tf.tensor2d(actor.training.inputs),
            tf.tensor2d(actor.training.labels),
            { epochs },
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
  --size: 30px;

  margin-top: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  user-select: none;
  outline: none;

  .field {
    .row {
      display: flex;

      .cell {
        display: flex;
        justify-content: center;
        align-items: center;
        width: var(--size);
        height: var(--size);
        font-size: 10px;
        color: #555;
      }
    }
  }

  .message {
    margin-top: 10px;
    text-align: center;
    color: gray;
  }

  .steps-count {
    text-align: center;
    color: gray;
  }

  .timer {
    font-size: 12px;
    color: dimgray;
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
