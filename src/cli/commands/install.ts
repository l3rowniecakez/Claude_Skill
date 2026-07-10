import type { Command } from 'commander';
import { join } from 'path';
import { homedir } from 'os';
import { existsSync, readdirSync, mkdirSync, copyFileSync, statSync } from 'fs';
import * as p from '@clack/prompts';

const ORACLE_CLI = 'arra-oracle-skills';
const DEFAULT_ORACLE_VERSION = '26.5.16';
const SKILLS_DIR = join(import.meta.dir, '../../skills');

async function installOracleSkills(profile: string, version: string, agent: string, yes: boolean) {
  const pkgRef = version ? `${ORACLE_CLI}@${version}` : ORACLE_CLI;
  const args = [pkgRef, 'install', '-g', '--profile', profile, '--agent', agent];
  if (yes) args.push('-y');

  p.log.step(`Running: bunx --bun ${args.join(' ')}`);

  const bunBin = process.execPath; // same bun binary that runs this script
  const proc = Bun.spawn([bunBin, 'x', '--bun', ...args], {
    stdout: 'inherit',
    stderr: 'inherit',
  });

  const exitCode = await proc.exited;
  if (exitCode !== 0) throw new Error(`arra-oracle-skills exited with code ${exitCode}`);
}

function copyDir(src: string, dest: string) {
  if (!existsSync(dest)) mkdirSync(dest, { recursive: true });
  for (const entry of readdirSync(src)) {
    const srcPath = join(src, entry);
    const destPath = join(dest, entry);
    if (statSync(srcPath).isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      copyFileSync(srcPath, destPath);
    }
  }
}

async function installOchiSkills(skillsRoot: string) {
  if (!existsSync(SKILLS_DIR)) {
    p.log.warn('No company skills found (src/skills/ is empty)');
    return;
  }

  const skills = readdirSync(SKILLS_DIR).filter((s) =>
    statSync(join(SKILLS_DIR, s)).isDirectory()
  );

  if (skills.length === 0) {
    p.log.warn('No company skills to install');
    return;
  }

  for (const skill of skills) {
    const src = join(SKILLS_DIR, skill);
    const dest = join(skillsRoot, skill);
    copyDir(src, dest);
    p.log.success(`Installed company skill: ${skill}`);
  }
}

export function registerInstall(program: Command, version: string) {
  program
    .command('install', { isDefault: true })
    .description('Install Oracle skills + Ochi company skills to Claude Code')
    .option('-p, --profile <name>', 'Oracle skill profile (minimal, standard, full, lab)', 'standard')
    .option('-y, --yes', 'Skip confirmation prompts')
    .option('--agent <name>', 'Target agent (claude-code, cursor, opencode, ...)', 'claude-code')
    .option('--oracle-version <ver>', `arra-oracle-skills version (empty = latest)`, DEFAULT_ORACLE_VERSION)
    .option('--oracle-only', 'Install Oracle skills only (skip company skills)')
    .option('--ochi-only', 'Install Ochi company skills only (skip Oracle)')
    .action(async (options) => {
      p.intro(`🔱 Ochi CLI v${version} — Skill Installer`);

      const skillsRoot = join(homedir(), '.claude', 'skills');

      try {
        if (!options.ochiOnly) {
          const verLabel = options.oracleVersion || 'latest';
          p.log.info(`Installing Oracle skills (profile: ${options.profile}, version: ${verLabel}, agent: ${options.agent})`);
          await installOracleSkills(options.profile, options.oracleVersion ?? '', options.agent, options.yes ?? false);
        }

        if (!options.oracleOnly) {
          p.log.info('Installing Ochi company skills...');
          await installOchiSkills(skillsRoot);
        }

        p.outro('✅ All skills installed successfully');
      } catch (err) {
        p.log.error(String(err));
        process.exit(1);
      }
    });
}
