import sys
import os
sys.path.append(".")

try:
    from agents.career_agent import CareerAgent
    agent = CareerAgent()
    
    state1 = {"phase":"interview","question_index":0,"answers":[],"characteristics":{"language":"unknown","documents":"unknown","residence":"unknown","work_permit":"unknown","discomforts":[]}}
    res1, next_state1 = agent.process("", session_state=state1, is_init=True)
    print(f"Step 1 | Phase: {next_state1['phase']} | Q_idx: {next_state1['question_index']} | Lang: {next_state1['characteristics']['language']}")
    
    res2, next_state2 = agent.process("нет", session_state=next_state1, is_init=False)
    print(f"Step 2 | Phase: {next_state2['phase']} | Q_idx: {next_state2['question_index']} | Lang: {next_state2['characteristics']['language']}")
    
    res3, next_state3 = agent.process("да", session_state=next_state2, is_init=False)
    print(f"Step 3 | Phase: {next_state3['phase']} | Q_idx: {next_state3['question_index']} | Lang: {next_state3['characteristics']['language']}")

except Exception as e:
    print(f"Error: {e}")
    try:
        import inspect
        from agents.career_agent import CareerAgent
        print("\nSource of CareerAgent.process:")
        print(inspect.getsource(CareerAgent.process))
        agent = CareerAgent()
        if hasattr(agent, "_is_no"):
            print(f"_is_no('нет'): {agent._is_no('нет')}")
    except Exception as e2:
        print(f"Inner Error: {e2}")