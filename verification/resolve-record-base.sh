#!/usr/bin/env bash
# Resolve the base commit the forward-only record gate (#172,
# spec/decisions/0012-record-path-hygiene-gate.md) diffs against.
#
# Inputs (env, plumbed by .github/workflows/signoff.yml):
#   EVENT        github.event_name (pull_request | push | merge_group | other)
#   PR_BASE_SHA  github.event.pull_request.base.sha
#   PUSH_BEFORE  github.event.before
#   MG_BASE      github.event.merge_group.base_sha
#
# Prints the resolved base SHA on stdout; diagnostics go to stderr with a
# ::error:: annotation.
#
# A merge_group run resolves its base from the event payload and FAILS
# CLOSED: an empty base, the literal "null", the zero SHA, a commit this
# checkout cannot see, or a base that is not an ancestor of HEAD is a hard
# error -- never a silent fallback to HEAD^, which would gate one commit of
# the merge queue's trial merge instead of the queue's real base..head
# range. Every other event keeps the pre-merge-queue behavior unchanged:
# the pull_request base wins, else the push "before" SHA, else
# (workflow_dispatch or an event without a base) the last commit.

zero_sha="0000000000000000000000000000000000000000"

emit_base() {
    if ! git rev-parse --verify "$1^{commit}" >/dev/null 2>&1; then
        echo "::error::no usable base commit ($1) for the forward-only record gate" >&2
        exit 1
    fi
    if ! git merge-base --is-ancestor "$1" HEAD 2>/dev/null; then
        echo "::error::base $1 is not an ancestor of HEAD; the changed-record range cannot be computed" >&2
        exit 1
    fi
    printf '%s\n' "$1"
}

if [ "${EVENT:-}" = "merge_group" ]; then
    base="${MG_BASE:-}"
    if [ -z "$base" ] || [ "$base" = "null" ] || [ "$base" = "$zero_sha" ]; then
        echo "::error::merge_group event carries no usable base_sha ($base) -- the forward-only record gate must gate the queue's base..head range, not fall back to HEAD^; refusing" >&2
        exit 1
    fi
    emit_base "$base"
    exit 0
fi

# Every other event: the pre-merge-queue chain, unchanged.
base="${PR_BASE_SHA:-}"
if [ -z "$base" ] || [ "$base" = "null" ]; then
    base="${PUSH_BEFORE:-}"
fi
if [ -z "$base" ] || [ "$base" = "null" ] || [ "$base" = "$zero_sha" ]; then
    # workflow_dispatch (or an event without a base): gate the last
    # commit. A root commit has no parent and fails below -- rightly.
    base="$(git rev-parse HEAD^)"
fi
emit_base "$base"
