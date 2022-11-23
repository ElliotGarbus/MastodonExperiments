import trio


async def child1():
    print("  child1: started! sleeping now...")
    await trio.sleep(2)
    print("  child1: exiting!")


async def child2():
    print("  child2: started! sleeping now...")
    await trio.sleep(5)
    print("  child2: exiting!")


async def parent():
    print("parent: started!")
    with trio.move_on_after(4) as cancel_scope:
        async with trio.open_nursery() as nursery:
            print("parent: spawning child1...")
            nursery.start_soon(child1)

            print("parent: spawning child2...")
            nursery.start_soon(child2)

            print("parent: waiting for children to finish...")
            # -- we exit the nursery block here --
    print(f'{cancel_scope.cancelled_caught=}')
    print("parent: all done!")


trio.run(parent)
