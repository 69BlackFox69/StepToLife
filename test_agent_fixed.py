import sys
import os
sys.path.append(".")

try:
    from agents.career_agent import CareerAgent
    agent = CareerAgent()
    
    state1 = {"phase":"interview","question_index":0,"answers":[],"characteristics":{"language":"unknown","documents":"unknown","residence":"unknown","work_permit":"unknown","discomforts":[]}}
    # CareerAgent.process returns a dict, not a tuple
    res_dict1 = agent.process("", session_state=state1, is_init=True)
    print(f"Step 1 | Phase: {res_dict1['phase']} | Q_idx: {res_dict1['question_index']} | Lang: {res_dict1['characteristics']['language']}")
    
    res_dict2 = agent.process("нет", session_state=res_dict1, is_init=False)
    print(f"Step 2 | Phase: {res_dict2['phase']} | Q_idx: {res_dict2['question_index']} | Lang: {res_dict2['characteristics']['language']}")
    
    res_dict3 = agent.process("да", session_state=res_dict2, is_init=False)
    print(f"Step 3 | Phase: {res_dict3['phase']} | Q_idx: {res_dict3['question_index']} | Lang: {res_dict3['characteristics']['language']}")

except Exception as e:
    print(f"Error: {e}")