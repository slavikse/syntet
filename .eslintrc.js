module.exports = {
  root: true,
  env: {
    node: true,
  },
  extends: [
    'plugin:vue/recommended',
    '@vue/airbnb',
  ],
  rules: {
    'no-console': 'off',
    'no-param-reassign': 'off',
    'object-curly-newline': 'off',
    'vue/no-use-v-if-with-v-for': 'error',
    'vue/no-v-html': 'warn',
    'vue/html-closing-bracket-spacing': 'error',
    'vue/prop-name-casing': 'error',
    'no-plusplus': 'off',
    'max-len': [1, 120, 2],
  },
  parserOptions: {
    parser: 'babel-eslint',
  },
};
