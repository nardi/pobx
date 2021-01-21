# PobX

Automated state management using transparent reactive programming constructs. A clone of [MobX](https://github.com/mobxjs/mobx) and built using [RxPy](https://github.com/ReactiveX/RxPY).

This project is just getting started. The aim is to follow the API and semantics of MobX as closely as possible.
The following core functionality has ben implemented (but likely not very robustly):

 - `observable` (for class members)
 - `observable.box` (for values)
 - `computed` (also `computedproperty` for properties)
 - `autorun`
 - `action`
 - `run_in_action`

See tests and the [MobX documentation](https://mobx.js.org/observable-state.html) for examples of usage.

Next up:

 - `observable` decorator for entire classes. Maybe also for existing objects?
 - Can `computedproperty` be absorbed into `computed`?
 - Is there a sensible way to deal with IO (e.g. asyncio)?
 - Typing.
 - Handling errors properly.
 - How to ensure subscriptions to observables are automatically terminated at an appropriate time? E.g. when calling `computed` in an observing function ([example from MobX](https://mobx.js.org/computeds-with-args.html)).
 - Documentation and intelligible code ;)
