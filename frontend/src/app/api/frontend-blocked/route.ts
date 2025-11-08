import { NextResponse } from 'next/server'

const blockedResponse = () =>
  NextResponse.json(
    { error: 'This endpoint is disabled in the web client.' },
    { status: 403 }
  )

export const GET = blockedResponse
export const POST = blockedResponse
export const PUT = blockedResponse
export const PATCH = blockedResponse
export const DELETE = blockedResponse
export const HEAD = blockedResponse
