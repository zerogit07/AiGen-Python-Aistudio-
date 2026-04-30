import asyncio
async def main():
  class B:
    async def execute(self): return 42
    def select(self): return self
  class A:
    def table(self): return B()
  supabase = A()
  res = await supabase.table().select().execute()
  print(res)
asyncio.run(main())