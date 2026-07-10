#!/usr/bin/env bun

import { program } from 'commander';
import pkg from '../../package.json' with { type: 'json' };

import { registerInstall } from './commands/install.js';

const VERSION = pkg.version;

program
  .name('ochi')
  .description('Ochi CLI — Oracle skills + company tools')
  .version(VERSION);

registerInstall(program, VERSION);

program.parse();
