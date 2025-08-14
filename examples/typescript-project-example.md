# TypeScript Project Example

This example shows how the Claude Code Kompendium works with a TypeScript project.

## Scenario

You're building a React component with TypeScript.

## Step 1: Write Code with Claude

```typescript
// You ask Claude: "Create a user profile component"
// Claude writes:

// UserProfile.tsx
import React from 'react';

interface UserProfileProps {
  user: {
    name: string;
    email: string;
    avatar?: string;
  };
}

export const UserProfile = ({ user }) => {  // ← Missing type annotation
  return (
    <div className="profile">
      <img src={user.avatar} alt={user.name} />
      <h2>{user.name}</h2>
      <p>{user.email}</p>
      <button onClick={handleEdit}>Edit</button>  // ← handleEdit not defined
    </div>
  );
};
```

## Step 2: Attempt Completion

```bash
Claude: "All done! The UserProfile component is ready to use."
```

## Step 3: Guardian Blocks

```
🛑 Cannot complete - 2 issues found:

📍 src/UserProfile.tsx:11:28
   TypeScript: Parameter 'user' implicitly has an 'any' type

📍 src/UserProfile.tsx:16:24
   TypeScript: Cannot find name 'handleEdit'

💡 Say 'fix the completion issues' to resolve
```

## Step 4: Request Fix

```bash
You: "Fix the completion issues"
```

## Step 5: Claude Fixes Precisely

```typescript
// Claude knows exactly what to fix:

import React from 'react';

interface UserProfileProps {
  user: {
    name: string;
    email: string;
    avatar?: string;
  };
}

export const UserProfile = ({ user }: UserProfileProps) => {  // ✅ Added type
  const handleEdit = () => {  // ✅ Defined function
    console.log('Edit clicked');
  };

  return (
    <div className="profile">
      <img src={user.avatar || '/default-avatar.png'} alt={user.name} />
      <h2>{user.name}</h2>
      <p>{user.email}</p>
      <button onClick={handleEdit}>Edit</button>
    </div>
  );
};
```

## Step 6: Retry Completion

```bash
Claude: "All done! The UserProfile component is ready."
Guardian: "✅ All checks passed - completion allowed"
```

## Step 7: Auto-Documentation Generated

File created: `docs/auto-generated/feature_20250114_153045.md`

```markdown
# Feature Documentation: User Profile Component

## Overview
**Generated**: 2025-01-14 15:30:45
**Session Duration**: 5.2 minutes

## Changes Summary
- Files Created: 1
- Lines Added: 24
- Components Added: 1

## New Components
- `UserProfile`

## Files Created
- `src/UserProfile.tsx`

## Usage
Import and use the component:
\```tsx
import { UserProfile } from './UserProfile';

<UserProfile user={{
  name: "John Doe",
  email: "john@example.com"
}} />
\```
```

## Step 8: Pattern Learned

The system now knows:
- You often forget type annotations on props
- You reference undefined functions
- These specific fixes work

Next time, Claude is less likely to make these mistakes!

## The Result

✅ **No broken code marked as complete**
✅ **Automatic documentation generated**
✅ **Pattern captured for future improvement**
✅ **Quick fix with no context loss**

This entire flow happens naturally without you thinking about quality checks, documentation, or learning - it just works!