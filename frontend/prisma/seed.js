const { PrismaClient } = require('@prisma/client');
const data = require('./mock-data.json');
const prisma = new PrismaClient();

const STATUS_MAP = {
  pending: 'applied',
  declined: 'rejected',
  decline: 'rejected',
  interview: 'interview',
  applied: 'applied',
  assessment: 'assessment',
  rejected: 'rejected',
  offer: 'offer',
  ghosted: 'ghosted',
  withdrawn: 'withdrawn',
};

const DROP = new Set([
  'inc',
  'llc',
  'ltd',
  'corp',
  'co',
  'company',
  'incorporated',
  'limited',
  'plc',
]);

function normalizeKey(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter((token) => token && !DROP.has(token))
    .join(' ');
}

function normalizeRole(value) {
  return normalizeKey(value)
    .replace(/\b(role|position|opening|opportunity)\b/g, ' ')
    .split(/\s+/)
    .filter(Boolean)
    .join(' ');
}

async function main() {
  const clerkId = 'user_2i6ZOgrlYTxxcqo26PlMfmt3Xiz';
  const jobs = data.map((job) => {
    return {
      position: job.position,
      company: job.company,
      location: job.location,
      status: STATUS_MAP[job.status] || 'applied',
      mode: job.mode,
      clerkId,
      source: 'manual',
      appliedAt: new Date(job.createdAt),
      createdAt: new Date(job.createdAt),
      companyKey: normalizeKey(job.company),
      roleKey: normalizeRole(job.position),
      statusManual: true,
    };
  });
  for (const job of jobs) {
    await prisma.job.create({
      data: job,
    });
  }
}
main()
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (e) => {
    console.error(e);
    await prisma.$disconnect();
    process.exit(1);
  });
