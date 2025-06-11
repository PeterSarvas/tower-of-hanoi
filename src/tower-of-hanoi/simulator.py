import json

class TowerOfHanoiSimulator:
    """
    Deterministic Tower of Hanoi simulator for rigorous solution validation.
    Implements the four-layer validation described in the paper.
    """
    
    def __init__(self, num_disks):
        self.num_disks = num_disks
        self.reset()
    
    def reset(self):
        """Reset to initial state: all disks on peg 0"""
        self.pegs = [
            list(range(self.num_disks, 0, -1)),  # Peg 0: largest to smallest
            [],  # Peg 1: empty
            []   # Peg 2: empty
        ]
        self.move_count = 0
        
    def get_goal_state(self):
        """Return the goal state: all disks on peg 2"""
        return [[], [], list(range(self.num_disks, 0, -1))]
    
    def validate_move(self, disk_id, from_peg, to_peg):
        """
        Four-layer validation as described in the paper:
        1. Peg boundary conditions (0-2)
        2. Source peg contains disks
        3. Specified disk is topmost
        4. Size ordering constraint
        """
        # Layer 1: Check peg boundary conditions
        if not (0 <= from_peg <= 2 and 0 <= to_peg <= 2):
            return False, f"Invalid peg indices: from_peg={from_peg}, to_peg={to_peg}"
        
        # Layer 2: Verify source peg contains disks
        if len(self.pegs[from_peg]) == 0:
            return False, f"Source peg {from_peg} is empty"
        
        # Layer 3: Confirm specified disk is topmost
        top_disk = self.pegs[from_peg][-1]
        if top_disk != disk_id:
            return False, f"Disk {disk_id} is not on top of peg {from_peg}. Top disk is {top_disk}"
        
        # Layer 4: Enforce size ordering constraint
        if len(self.pegs[to_peg]) > 0:
            target_top = self.pegs[to_peg][-1]
            if disk_id > target_top:
                return False, f"Cannot place larger disk {disk_id} on smaller disk {target_top}"
        
        return True, "Valid move"
    
    def execute_move(self, disk_id, from_peg, to_peg):
        """Execute a validated move"""
        is_valid, error_msg = self.validate_move(disk_id, from_peg, to_peg)
        if not is_valid:
            return False, error_msg
        
        # Execute the move
        disk = self.pegs[from_peg].pop()
        self.pegs[to_peg].append(disk)
        self.move_count += 1
        
        return True, "Move executed successfully"
    
    def is_solved(self):
        """Check if puzzle is in goal state"""
        goal = self.get_goal_state()
        return self.pegs == goal
    
    def validate_complete_solution(self, solution):
        """
        Validate complete solution and provide detailed analysis.
        Returns comprehensive feedback about where and why solution fails.
        """
        self.reset()
        
        analysis = {
            "total_moves": len(solution),
            "valid_moves": 0,
            "invalid_moves": 0,
            "first_invalid_move": None,
            "final_state": None,
            "goal_achieved": False,
            "move_details": [],
            "error_summary": []
        }
        
        for i, move_str in enumerate(solution):
            try:
                # Parse move - expect format like "[1, 0, 2]" or "1,0,2"
                move = self.parse_move(move_str)
                if not move:
                    analysis["move_details"].append({
                        "move_index": i,
                        "move_string": move_str,
                        "status": "parsing_error",
                        "error": "Could not parse move format"
                    })
                    analysis["invalid_moves"] += 1
                    if analysis["first_invalid_move"] is None:
                        analysis["first_invalid_move"] = i
                    continue
                
                disk_id, from_peg, to_peg = move
                
                # Validate and execute move
                is_valid, message = self.execute_move(disk_id, from_peg, to_peg)
                
                move_detail = {
                    "move_index": i,
                    "move_string": move_str,
                    "parsed_move": move,
                    "status": "valid" if is_valid else "invalid",
                    "message": message,
                    "state_after": [peg[:] for peg in self.pegs]  # Deep copy
                }
                
                analysis["move_details"].append(move_detail)
                
                if is_valid:
                    analysis["valid_moves"] += 1
                else:
                    analysis["invalid_moves"] += 1
                    analysis["error_summary"].append(f"Move {i}: {message}")
                    if analysis["first_invalid_move"] is None:
                        analysis["first_invalid_move"] = i
                    break  # Stop at first invalid move
                    
            except Exception as e:
                analysis["move_details"].append({
                    "move_index": i,
                    "move_string": move_str,
                    "status": "error",
                    "error": str(e)
                })
                analysis["invalid_moves"] += 1
                if analysis["first_invalid_move"] is None:
                    analysis["first_invalid_move"] = i
                break
        
        # Final state analysis
        analysis["final_state"] = [peg[:] for peg in self.pegs]
        analysis["goal_achieved"] = self.is_solved()
        
        return analysis
    
    def parse_move(self, move_str):
        """Parse move string into (disk_id, from_peg, to_peg) tuple"""
        try:
            # Remove whitespace and brackets
            clean_str = move_str.strip().strip('[](){}')
            
            # Try to parse as JSON first
            try:
                move = json.loads(f"[{clean_str}]")
                if len(move) == 3:
                    return tuple(move)
            except:
                pass
            
            # Try comma-separated parsing
            parts = [x.strip() for x in clean_str.split(',')]
            if len(parts) == 3:
                return tuple(int(x) for x in parts)
            
            # Try space-separated parsing
            parts = clean_str.split()
            if len(parts) == 3:
                return tuple(int(x) for x in parts)
                
        except Exception:
            pass
        
        return None