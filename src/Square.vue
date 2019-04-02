<template>
  <div>
    <div class="stat generation">
      Живых: {{ alives }} | Поколений: {{ generation }} | Победы: {{ victories }}
      <br>
      Максимальное значение ячейки: {{ investigatedMaximumCellValue }}
    </div>

    <div
      ref="Square"
      class="Square"
      tabindex="0"
      @keyup.up="handJumpTop"
      @keyup.right="handJumpRight"
      @keyup.down="handJumpBottom"
      @keyup.left="handJumpLeft"
    >
      <div class="cells field">
        <div
          v-for="(cellValue, index) in field"
          :key="index"
          :data-cell-value="cellValue"
          :class="['cell', { 'available': cellValue !== 0 }]"
        >
          <div
            v-if="cellValue === 1"
            class="starting-checkpoint"
          >
            👋🏻
          </div>

          <div
            v-if="cellValue === investigatedMaximumCellValue"
            class="maximum-cell-value-checkpoint"
          >
            🤟
          </div>

          <div
            v-if="cellValue === maximumCellValue"
            class="finishing-checkpoint"
          >
            💯
          </div>
        </div>
      </div>

      <div class="actors field">
        <div
          v-for="actor in actors"
          :key="actor.id"
          :style="{
            gridRow: actor.y,
            gridColumn: actor.x,
          }"
        >
          <div
            :ref="`actors_${actor.id}`"
            class="actor"
          >
            <div>🏃️</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as tf from '@tensorflow/tfjs';
import nanoid from 'nanoid';
import cloneDeep from 'clone-deep';

const actorsDefault = [];
const actorsCount = 1000;
// Каждый N будет исследователем.
const eachNumber = 100;
const automaticControl = true;

/* eslint-disable no-plusplus */
for (let i = 0; i < actorsCount; i++) {
  actorsDefault.push({
    id: nanoid(10),
    x: 2,
    y: 2,
    alive: true,
    cellValue: 0,
    step: 0,
    style: undefined,
  });
}

export default {
  name: 'Square',

  data() {
    return {
      model: tf.sequential(),
      // Очищаемое поколение всех актёров перед следующим поколением.
      training: {
        inputs: [],
        labels: [],
      },
      // Набор лучших поколений из нескольких в training.
      learning: {
        // x, y - Нормализованные координаты актёра.
        // cellValue - Количество шагов, сделанных от стартовой позиции.
        inputs: [],
        // [1, 0, 0, 0] - Пойти на север (north).
        // [0, 1, 0, 0] - Пойти на восток (east).
        // [0, 0, 1, 0] - Пойти на юг (south).
        // [0, 0, 0, 1] - Пойти на запад (west).
        labels: [],
      },
      generation: 0,
      victories: 0,

      // Набор генерируемых актёров.
      actors: [],
      // Актёры оставшиеся в живых.
      alives: -1,
      // Самое максимальное значение пройденной ячейки.
      investigatedMaximumCellValue: 1,

      // Игровая область обязательно квадратной формы, для Math.sqrt(this.field.length).
      // Обязательно между доступным путём, должно быть 2 запретных ячейки
      // из за исследовательских "усиков".
      // 0 - Запретная территория.
      // [1..N) - Проходная территория.
      // N - Финишная точка.
      // @formatter:off
      /* eslint-disable no-multi-spaces */
      field: [
        0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
        0,  1,  0,  0,  0,  0,  0,  0,  0, 45, 44, 43,  0,
        0,  2,  0,  0,  0,  0,  0,  0,  0,  0,  0, 42,  0,
        0,  3,  0,  0,  8,  9, 10, 11,  0,  0,  0, 41,  0,
        0,  4,  5,  6,  7,  0,  0, 12,  0,  0,  0, 40,  0,
        0,  0,  0,  0,  0,  0,  0, 13,  0,  0,  0, 39,  0,
        0,  0,  0,  0,  0,  0, 15, 14,  0,  0,  0, 38,  0,
        0,  0,  0,  0,  0,  0, 16,  0,  0,  0,  0, 37,  0,
        0,  0, 21, 20, 19, 18, 17,  0,  0,  0,  0, 36,  0,
        0,  0, 22,  0,  0,  0,  0,  0,  0, 33, 34, 35,  0,
        0,  0, 23,  0,  0,  0,  0,  0,  0, 32,  0,  0,  0,
        0,  0, 24, 25, 26, 27, 28, 29, 30, 31,  0,  0,  0,
        0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
      ],
      // @formatter:on
      /* eslint-enable no-multi-spaces */
      fieldStyle: undefined,
      fieldSize: -1,
      maximumCellValue: -1,
      maximumSteps: -1,
    };
  },

  async mounted() {
    this.fieldSetting();
    this.setupModel();

    await this.actorsReset();

    if (automaticControl) {
      await this.modelPredict();
    }
  },

  methods: {
    fieldSetting() {
      this.fieldStyle = this.$refs.Square.style;
      this.fieldSize = Math.sqrt(this.field.length);
      this.maximumCellValue = Math.max(...this.field);
      this.maximumSteps = this.maximumCellValue;

      this.fieldStyle.setProperty('--quantity-rows', this.fieldSize);
      this.fieldStyle.setProperty('--quantity-columns', this.fieldSize);
    },

    setupModel() {
      this.model.add(tf.layers.dense({
        // Описание в learning.inputs.
        inputShape: [3],
        activation: 'sigmoid',
        units: 128,
      }));

      // this.model.add(tf.layers.dense({
      //   activation: 'sigmoid',
      //   units: 64,
      // }));

      this.model.add(tf.layers.dense({
        activation: 'sigmoid',
        // [north, east, south, west] - Прогноз стороны для передвижения.
        units: 4,
      }));

      this.model.compile({
        optimizer: tf.train.adam(0.01),
        loss: 'meanSquaredError',
        metrics: ['accuracy'],
      });
    },

    async actorsReset() {
      this.actors = cloneDeep(actorsDefault);
      await this.$nextTick();

      this.actors.forEach((actor) => {
        const [{ style }] = this.$refs[`actors_${actor.id}`];
        actor.style = style;
      });
    },

    async modelPredict() {
      await Promise.all(this.actors.map(async (actor, index) => {
        if (actor.alive) {
          let prediction;

          // Создание случайных решений для исследователей.
          if (index % eachNumber === 0) {
            const jumpTop = Math.random();
            const jumpRight = Math.random();
            const jumpBottom = Math.random();
            const jumpLeft = Math.random();

            prediction = [jumpTop, jumpRight, jumpBottom, jumpLeft];
          } else {
            prediction = await this.model.predict(tf.tensor2d([
              [
                actor.x / this.fieldSize,
                actor.y / this.fieldSize,
                actor.cellValue / this.maximumCellValue,
              ],
            ])).data();

            // console.log(
            //   'Top', prediction[0].toFixed(10),
            //   'Right', prediction[1].toFixed(10),
            //   'Bottom', prediction[2].toFixed(10),
            //   'Left', prediction[3].toFixed(10),
            // );
          }

          const directionStep = this.getDirectionStep(prediction);
          this[directionStep](actor);

          await this.availabilityCheck(actor);
        }

        // Замедление прогноза для каждого актёра.
        // await new Promise((resolve) => {
        //   setTimeout(() => {
        //     resolve();
        //   }, 1000);
        // });
      }));

      this.actors = this.actors.filter(({ alive }) => alive);
      await this.modelPredict();
    },

    getDirectionStep([jumpTop, jumpRight, jumpBottom, jumpLeft]) {
      let maximum = jumpTop;
      let action = 'jumpTop';

      if (jumpRight > maximum) {
        maximum = jumpRight;
        action = 'jumpRight';
      }

      if (jumpBottom > maximum) {
        maximum = jumpBottom;
        action = 'jumpBottom';
      }

      if (jumpLeft > maximum) {
        // maximum = jumpLeft;
        action = 'jumpLeft';
      }

      return action;
    },

    jumpTop(actor) {
      actor.y -= 1;
    },

    jumpRight(actor) {
      actor.x += 1;
    },

    jumpBottom(actor) {
      actor.y += 1;
    },

    jumpLeft(actor) {
      actor.x -= 1;
    },

    async availabilityCheck(actor) {
      // Смещение на -1: Сетка начинается с 1, а значения в массиве начинаются с 0.
      const normalY = actor.y - 1;
      const normalX = actor.x - 1;
      const cellValue = this.field[normalY * this.fieldSize + normalX];
      const label = this.getAntennaCellValues({ normalX, normalY });

      // Сброс при успешном прохождении.
      let isReset = false;

      switch (true) {
        case cellValue === 0:
          actor.alive = false;
          break;

        case cellValue > 0 && cellValue < this.maximumCellValue:
          actor.cellValue = cellValue;
          actor.step += 1;

          if (actor.step === this.maximumSteps) {
            actor.alive = false;
          }
          break;

        case cellValue === this.maximumCellValue:
          isReset = true;
          actor.cellValue = cellValue;
          actor.step += 1;
          actor.alive = false;
          this.victories += 1;
          break;

        default:
      }

      if (cellValue > this.investigatedMaximumCellValue) {
        this.investigatedMaximumCellValue = cellValue;
      }

      this.saveTraining({ actor, label });

      this.alives = this.actors.filter(({ alive }) => alive).length;

      if (this.alives === 0) {
        await this.modelFit();
      }

      if (isReset) {
        await this.actorsReset();
      }
    },

    // Получение значения ячейки, чем дальше ячейка от старта, тем больше там значение.
    getAntennaCellValues({ normalX, normalY }) {
      // 0 - когда выходит за пределы поля (дальше пути нет).
      const topCellValue = this.field[(normalY - 1) * this.fieldSize + normalX] || 0;
      const rightCellValue = this.field[normalY * this.fieldSize + (normalX + 1)] || 0;
      const bottomCellValue = this.field[(normalY + 1) * this.fieldSize + normalX] || 0;
      const leftCellValue = this.field[normalY * this.fieldSize + (normalX - 1)] || 0;

      return [
        topCellValue / this.maximumCellValue,
        rightCellValue / this.maximumCellValue,
        bottomCellValue / this.maximumCellValue,
        leftCellValue / this.maximumCellValue,
      ];
    },

    saveTraining({ actor, label }) {
      this.training.inputs.push([
        actor.x / this.fieldSize,
        actor.y / this.fieldSize,
        actor.cellValue / this.maximumCellValue,
      ]);

      this.training.labels.push(label);
    },

    async modelFit() {
      const {
        firstInput,
        firstLabel,

        secondInput,
        secondLabel,

        thirdInput,
        thirdLabel,

        fourInput,
        fourLabel,

        fiveInput,
        fiveLabel,
      } = this.getBestMoves();

      await this.model.fit(
        tf.tensor2d([
          firstInput,
          secondInput,
          thirdInput,
          fourInput,
          fiveInput,
        ]),

        tf.tensor2d([
          firstLabel,
          secondLabel,
          thirdLabel,
          fourLabel,
          fiveLabel,
        ]),
      );

      // this.learning.inputs.push(
      //   firstInput,
      //   secondInput,
      //   thirdInput,
      //   fourInput,
      //   fiveInput,
      // );
      //
      // this.learning.labels.push(
      //   firstLabel,
      //   secondLabel,
      //   thirdLabel,
      //   fourLabel,
      //   fiveLabel,
      // );

      // await this.model.fit(
      //   this.learning.inputs,
      //   this.learning.labels,
      // );

      this.generation += 1;
      await this.actorsReset();
    },

    getBestMoves() {
      const { inputs, labels } = this.training;
      this.training = { inputs: [], labels: [] };

      let fiveCellValue = -1;
      let fourCellValue = -1;
      let thirdCellValue = -1;
      let secondCellValue = -1;
      let firstCellValue = -1;

      let fiveIndex = -1;
      let fourIndex = -1;
      let thirdIndex = -1;
      let secondIndex = -1;
      let firstIndex = -1;

      inputs.forEach(([, , cellValue], index) => {
        switch (true) {
          case cellValue > firstCellValue:
            fiveCellValue = fourCellValue;
            fourCellValue = thirdCellValue;
            thirdCellValue = secondCellValue;
            secondCellValue = firstCellValue;
            firstCellValue = cellValue;

            fiveIndex = fourIndex;
            fourIndex = thirdIndex;
            thirdIndex = secondIndex;
            secondIndex = firstIndex;
            firstIndex = index;
            break;

          case cellValue > secondCellValue:
            fiveCellValue = fourCellValue;
            fourCellValue = thirdCellValue;
            thirdCellValue = secondCellValue;
            secondCellValue = cellValue;

            fiveIndex = fourIndex;
            fourIndex = thirdIndex;
            thirdIndex = secondIndex;
            secondIndex = index;
            break;

          case cellValue > thirdCellValue:
            fiveCellValue = fourCellValue;
            fourCellValue = thirdCellValue;
            thirdCellValue = cellValue;

            fiveIndex = fourIndex;
            fourIndex = thirdIndex;
            thirdIndex = index;
            break;

          case cellValue > fourCellValue:
            fiveCellValue = fourCellValue;
            fourCellValue = cellValue;

            fiveIndex = fourIndex;
            fourIndex = index;
            break;

          case cellValue > fiveCellValue:
            fiveCellValue = cellValue;

            fiveIndex = index;
            break;

          default:
        }
      });

      return {
        firstInput: inputs[firstIndex],
        firstLabel: labels[firstIndex],

        secondInput: inputs[secondIndex],
        secondLabel: labels[secondIndex],

        thirdInput: inputs[thirdIndex],
        thirdLabel: labels[thirdIndex],

        fourInput: inputs[fourIndex],
        fourLabel: labels[fourIndex],

        fiveInput: inputs[fiveIndex],
        fiveLabel: labels[fiveIndex],
      };
    },

    // Специально для ручного управления.
    async handJumpTop() {
      const [actor] = this.actors;

      this.jumpTop(actor);
      await this.availabilityCheck(actor);
    },

    async handJumpRight() {
      const [actor] = this.actors;

      this.jumpRight(actor);
      await this.availabilityCheck(actor);
    },

    async handJumpBottom() {
      const [actor] = this.actors;

      this.jumpBottom(actor);
      await this.availabilityCheck(actor);
    },

    async handJumpLeft() {
      const [actor] = this.actors;

      this.jumpLeft(actor);
      await this.availabilityCheck(actor);
    },
  },
};
</script>

<style scoped>
.Square {
  --quantity-rows: -1;
  --quantity-columns: -1;
  --column-width: 3rem;

  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  outline: none;
  user-select: none;
}

.stat {
  position: absolute;
  z-index: 1;
  font-size: 1.2rem;
  color: white;
}

.generation {
  margin-top: 1rem;
  width: 100%;
  text-align: center;
}

.cells {
}

.cell {
  position: relative;
  display: flex;
  background-color: #222;
}

.available {
  background-color: darkcyan;
}

.starting-checkpoint,
.maximum-cell-value-checkpoint,
.finishing-checkpoint {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100%;
  font-size: 2rem;
  background-color: seagreen;
  outline: 0.5rem dashed seagreen;
}

.maximum-cell-value-checkpoint {
  background-color: brown;
  outline: 0.5rem dashed brown;
}

.field {
  display: grid;
  grid-template-rows: repeat(var(--quantity-rows), var(--column-width));
  grid-template-columns: repeat(var(--quantity-columns), var(--column-width));
  grid-gap: 0.5rem;
}

.actors {
  position: absolute;
}

.actor {
  height: 100%;
  width: 100%;
  text-align: center;
  font-size: 2rem;
  background-color: yellow;
  outline: 0.5rem dashed yellow;
}
</style>
