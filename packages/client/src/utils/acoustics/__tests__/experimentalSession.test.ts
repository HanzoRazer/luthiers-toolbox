/**
 * Experimental Session Tests
 *
 * Dev Order 85: Session continuity layer for Measurement Lab
 */
import { describe, it, expect } from 'vitest';
import {
  createExperimentalSession,
  appendArchiveToSession,
  sortSessionArchives,
  buildSessionSummary,
  linkVariantToSession,
} from '../experimentalSession';
import type { ExperimentalSessionRecord } from '@/types/acoustics/experimentalSession';
import { EXPERIMENTAL_SESSION_SCHEMA_VERSION } from '@/types/acoustics/experimentalSession';
import type { MeasurementArchiveRecordRecord } from '@/types/acoustics/measurementArchive';

// Fixed timestamp for deterministic tests
const FIXED_DATE = new Date('2026-05-24T14:30:00.000Z');

// Test fixture for MeasurementArchiveRecordRecord
function createTestArchive(
  archiveId: string,
  createdAtIso: string
): MeasurementArchiveRecordRecord {
  return {
    archiveId,
    kind: 'measurement-archive',
    metadata: {
      schemaVersion: 'measurement-archive.v1',
      createdAtIso,
      sourceApplication: 'test',
    },
    context: {
      referenceLabel: `Archive ${archiveId}`,
    },
    sections: [],
  };
}

describe('Dev Order 85: Experimental Session Continuity Layer', () => {
  describe('createExperimentalSession', () => {
    it('creates session with required fields', () => {
      const session = createExperimentalSession('Test Session', {}, FIXED_DATE);

      expect(session.title).toBe('Test Session');
      expect(session.sessionId).toBe('experimental-session-20260524-143000');
      expect(session.schemaVersion).toBe(EXPERIMENTAL_SESSION_SCHEMA_VERSION);
      expect(session.archiveIds).toEqual([]);
      expect(session.variantIds).toEqual([]);
    });

    it('includes optional objective, constraints, and notes', () => {
      const session = createExperimentalSession(
        'Cedar vs Spruce',
        {
          objective: 'Compare tap tone response',
          constraints: 'Same humidity, same mallet',
          notes: 'Initial test run',
        },
        FIXED_DATE
      );

      expect(session.objective).toBe('Compare tap tone response');
      expect(session.constraints).toBe('Same humidity, same mallet');
      expect(session.notes).toBe('Initial test run');
    });

    it('sets startedAt and updatedAt to same timestamp on creation', () => {
      const session = createExperimentalSession('Test', {}, FIXED_DATE);

      expect(session.startedAt).toBe('2026-05-24T14:30:00.000Z');
      expect(session.updatedAt).toBe('2026-05-24T14:30:00.000Z');
    });

    it('generates unique session IDs for different timestamps', () => {
      const session1 = createExperimentalSession(
        'Test 1',
        {},
        new Date('2026-05-24T14:30:00.000Z')
      );
      const session2 = createExperimentalSession(
        'Test 2',
        {},
        new Date('2026-05-24T14:31:00.000Z')
      );

      expect(session1.sessionId).not.toBe(session2.sessionId);
    });
  });

  describe('appendArchiveToSession', () => {
    it('appends archive ID to session', () => {
      const session = createExperimentalSession('Test', {}, FIXED_DATE);
      const updated = appendArchiveToSession(
        session,
        'archive-001',
        new Date('2026-05-24T15:00:00.000Z')
      );

      expect(updated.archiveIds).toEqual(['archive-001']);
      expect(updated.updatedAt).toBe('2026-05-24T15:00:00.000Z');
    });

    it('preserves archive order (iteration order)', () => {
      let session = createExperimentalSession('Test', {}, FIXED_DATE);
      session = appendArchiveToSession(session, 'first', FIXED_DATE);
      session = appendArchiveToSession(session, 'second', FIXED_DATE);
      session = appendArchiveToSession(session, 'third', FIXED_DATE);

      expect(session.archiveIds).toEqual(['first', 'second', 'third']);
    });

    it('does not duplicate existing archive ID', () => {
      let session = createExperimentalSession('Test', {}, FIXED_DATE);
      session = appendArchiveToSession(session, 'archive-001', FIXED_DATE);
      const beforeAppend = session;
      session = appendArchiveToSession(session, 'archive-001', FIXED_DATE);

      expect(session.archiveIds).toEqual(['archive-001']);
      expect(session).toBe(beforeAppend); // Same reference — no mutation
    });

    it('is immutable — does not mutate input session', () => {
      const original = createExperimentalSession('Test', {}, FIXED_DATE);
      const originalArchiveIds = original.archiveIds;
      appendArchiveToSession(original, 'new-archive', FIXED_DATE);

      expect(original.archiveIds).toBe(originalArchiveIds);
      expect(original.archiveIds).toEqual([]);
    });
  });

  describe('sortSessionArchives', () => {
    it('sorts archives by capturedAt timestamp', () => {
      let session = createExperimentalSession('Test', {}, FIXED_DATE);
      session = appendArchiveToSession(session, 'late', FIXED_DATE);
      session = appendArchiveToSession(session, 'early', FIXED_DATE);
      session = appendArchiveToSession(session, 'middle', FIXED_DATE);

      const archives = new Map<string, MeasurementArchiveRecord>([
        ['early', createTestArchive('early', '2026-05-24T10:00:00.000Z')],
        ['middle', createTestArchive('middle', '2026-05-24T12:00:00.000Z')],
        ['late', createTestArchive('late', '2026-05-24T14:00:00.000Z')],
      ]);

      const sorted = sortSessionArchives(session, archives, FIXED_DATE);

      expect(sorted.archiveIds).toEqual(['early', 'middle', 'late']);
    });

    it('returns same session if order unchanged', () => {
      let session = createExperimentalSession('Test', {}, FIXED_DATE);
      session = appendArchiveToSession(session, 'first', FIXED_DATE);
      session = appendArchiveToSession(session, 'second', FIXED_DATE);

      const archives = new Map<string, MeasurementArchiveRecord>([
        ['first', createTestArchive('first', '2026-05-24T10:00:00.000Z')],
        ['second', createTestArchive('second', '2026-05-24T12:00:00.000Z')],
      ]);

      const sorted = sortSessionArchives(session, archives, FIXED_DATE);

      expect(sorted).toBe(session); // Same reference — no change
    });

    it('handles missing archives gracefully', () => {
      let session = createExperimentalSession('Test', {}, FIXED_DATE);
      session = appendArchiveToSession(session, 'exists', FIXED_DATE);
      session = appendArchiveToSession(session, 'missing', FIXED_DATE);

      const archives = new Map<string, MeasurementArchiveRecord>([
        ['exists', createTestArchive('exists', '2026-05-24T10:00:00.000Z')],
      ]);

      const sorted = sortSessionArchives(session, archives, FIXED_DATE);

      // Missing archives sort after existing ones (sort returns 1 for missing)
      expect(sorted.archiveIds[0]).toBe('exists');
      expect(sorted.archiveIds[1]).toBe('missing');
    });
  });

  describe('buildSessionSummary', () => {
    it('returns summary with archive and variant counts', () => {
      let session = createExperimentalSession('Test', {}, FIXED_DATE);
      session = appendArchiveToSession(session, 'a1', FIXED_DATE);
      session = appendArchiveToSession(session, 'a2', FIXED_DATE);
      session = linkVariantToSession(session, 'v1', FIXED_DATE);

      const archives = new Map<string, MeasurementArchiveRecord>([
        ['a1', createTestArchive('a1', '2026-05-24T10:00:00.000Z')],
        ['a2', createTestArchive('a2', '2026-05-24T12:00:00.000Z')],
      ]);

      const summary = buildSessionSummary(session, archives);

      expect(summary.sessionId).toBe(session.sessionId);
      expect(summary.title).toBe('Test');
      expect(summary.archiveCount).toBe(2);
      expect(summary.variantCount).toBe(1);
    });

    it('computes date range from archives', () => {
      let session = createExperimentalSession('Test', {}, FIXED_DATE);
      session = appendArchiveToSession(session, 'a1', FIXED_DATE);
      session = appendArchiveToSession(session, 'a2', FIXED_DATE);

      const archives = new Map<string, MeasurementArchiveRecord>([
        ['a1', createTestArchive('a1', '2026-05-20T10:00:00.000Z')],
        ['a2', createTestArchive('a2', '2026-05-24T12:00:00.000Z')],
      ]);

      const summary = buildSessionSummary(session, archives);

      expect(summary.dateRange.earliest).toBe('2026-05-20T10:00:00.000Z');
      expect(summary.dateRange.latest).toBe('2026-05-24T12:00:00.000Z');
      expect(summary.durationDays).toBe(4);
    });

    it('returns null date range for empty session', () => {
      const session = createExperimentalSession('Test', {}, FIXED_DATE);
      const archives = new Map<string, MeasurementArchiveRecord>();

      const summary = buildSessionSummary(session, archives);

      expect(summary.dateRange.earliest).toBeNull();
      expect(summary.dateRange.latest).toBeNull();
      expect(summary.durationDays).toBeNull();
    });

    it('handles archives without createdAtIso', () => {
      let session = createExperimentalSession('Test', {}, FIXED_DATE);
      session = appendArchiveToSession(session, 'a1', FIXED_DATE);

      const archiveWithoutTimestamp = {
        archiveId: 'a1',
        kind: 'measurement-archive',
        metadata: {
          schemaVersion: 'measurement-archive.v1',
          createdAtIso: undefined as unknown as string,
          sourceApplication: 'test',
        },
        context: {},
        sections: [],
      } as MeasurementArchiveRecord;

      const archives = new Map<string, MeasurementArchiveRecord>([
        ['a1', archiveWithoutTimestamp],
      ]);

      const summary = buildSessionSummary(session, archives);

      expect(summary.archiveCount).toBe(1);
      expect(summary.dateRange.earliest).toBeNull();
    });
  });

  describe('linkVariantToSession', () => {
    it('links variant ID to session', () => {
      const session = createExperimentalSession('Test', {}, FIXED_DATE);
      const updated = linkVariantToSession(
        session,
        'topology-variant-20260524-100000',
        new Date('2026-05-24T15:00:00.000Z')
      );

      expect(updated.variantIds).toEqual(['topology-variant-20260524-100000']);
      expect(updated.updatedAt).toBe('2026-05-24T15:00:00.000Z');
    });

    it('does not duplicate existing variant ID', () => {
      let session = createExperimentalSession('Test', {}, FIXED_DATE);
      session = linkVariantToSession(
        session,
        'topology-variant-20260524-100000',
        FIXED_DATE
      );
      const beforeLink = session;
      session = linkVariantToSession(
        session,
        'topology-variant-20260524-100000',
        FIXED_DATE
      );

      expect(session.variantIds).toHaveLength(1);
      expect(session).toBe(beforeLink);
    });

    it('is immutable — does not mutate input session', () => {
      const original = createExperimentalSession('Test', {}, FIXED_DATE);
      const originalVariantIds = original.variantIds;
      linkVariantToSession(original, 'new-variant', FIXED_DATE);

      expect(original.variantIds).toBe(originalVariantIds);
      expect(original.variantIds).toEqual([]);
    });
  });

  describe('observational semantics', () => {
    it('session record has no recommendation fields', () => {
      const session = createExperimentalSession('Test', {}, FIXED_DATE);

      // TypeScript enforces this, but verify at runtime
      const keys = Object.keys(session);
      const forbiddenFields = [
        'recommendation',
        'recommended',
        'suggests',
        'better',
        'optimal',
        'correct',
      ];

      for (const field of forbiddenFields) {
        expect(keys).not.toContain(field);
      }
    });

    it('summary has no recommendation fields', () => {
      const session = createExperimentalSession('Test', {}, FIXED_DATE);
      const summary = buildSessionSummary(
        session,
        new Map<string, MeasurementArchiveRecord>()
      );

      const keys = Object.keys(summary);
      const forbiddenFields = [
        'recommendation',
        'recommended',
        'suggests',
        'better',
        'optimal',
        'correct',
      ];

      for (const field of forbiddenFields) {
        expect(keys).not.toContain(field);
      }
    });
  });

  describe('schema version', () => {
    it('session includes schema version for migration support', () => {
      const session = createExperimentalSession('Test', {}, FIXED_DATE);

      expect(session.schemaVersion).toBe('experimental-session.v1');
    });
  });

  describe('session ID format', () => {
    it('follows experimental-session-YYYYMMDD-HHmmss pattern', () => {
      const session = createExperimentalSession(
        'Test',
        {},
        new Date('2026-12-31T23:59:59.000Z')
      );

      expect(session.sessionId).toBe('experimental-session-20261231-235959');
    });

    it('pads single-digit values', () => {
      const session = createExperimentalSession(
        'Test',
        {},
        new Date('2026-01-05T09:05:03.000Z')
      );

      expect(session.sessionId).toBe('experimental-session-20260105-090503');
    });
  });
});
