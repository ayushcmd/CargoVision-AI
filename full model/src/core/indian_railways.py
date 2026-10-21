class IndianWagonParser:
    """
    Parses 11-digit Indian Railways Wagon Numbers.
    Format:
    C1 C2       : Wagon Type
    C3 C4       : Owning Railway
    C5 C6       : Year of Manufacture
    C7 C8 C9 C10: Unique ID
    C11         : Check Digit
    """
    
    WAGON_TYPES = {
        '10': 'BOXN', '11': 'BOXNHA', '12': 'BOXNHS', '13': 'BOXNCR', '14': 'BOXNLW',
        '15': 'BOXNB', '16': 'BOXNF', '17': 'BOXNG', '18': 'BOY', '19': 'BOST',
        '20': 'BOXNAL', '21': 'BOXN-HS', '22': 'BOXNHL', '23': 'BOXNHL','24': 'BOXNS',
        '30': 'BCN', '31': 'BCNA', '32': 'BCNAHS', '40': 'BTPN', '41': 'BTPGLN',
        '42': 'BTALN', '43': 'BTCS', '44': 'BTPH', '45': 'BTAP', '46': 'BTFLN', 
        '70': 'BOBYN', '72': 'BOBRN', '80': 'BWTB', '85': 'BVZC',
        # Add more mappings as needed
    }

    RAILWAY_CODES = {
        '01': 'CR', '02': 'ER', '03': 'NR', '04': 'NER', '05': 'NFR', '06': 'SR',
        '07': 'SER', '08': 'WR', '09': 'SCR', '10': 'ECR', '11': 'NWR', 
        '12': 'ECoR', '13': 'NCR', '14': 'SECR', '15': 'SWR', '16': 'WCR',
        '24': 'MoD', '25': 'CONCOR', '26': 'Private'  # Add these missing ones
    }

    @staticmethod
    def parse(number_str):
        # Clean input: remove spaces, non-digits
        clean_num = ''.join(filter(str.isdigit, number_str))
        
        if len(clean_num) != 11:
            return None # Not a valid 11-digit code

        c1_c2 = clean_num[0:2]
        c3_c4 = clean_num[2:4]
        c5_c6 = clean_num[4:6]
        c7_c10 = clean_num[6:10]
        c11 = clean_num[10]

        wagon_type = IndianWagonParser.WAGON_TYPES.get(c1_c2, "Unknown")
        railway = IndianWagonParser.RAILWAY_CODES.get(c3_c4, "Unknown")
        
        # Year logic: 00-99. Assuming 2000+? Or 1900? 
        # Usually contextual, but let's just return the raw YY
        year_mfg = f"20{c5_c6}" # Approximation suitable for modern wagons
        
        # Check Digit Validation (Standard approach involves specific weights, 
        # but for now we just parse. We can implement Luhn or specific algo if specs provided)
        
        return {
            "original": clean_num,
            "formatted": f"{c1_c2} {c3_c4} {c5_c6} {c7_c10} {c11}",
            "type": wagon_type,
            "railway": railway,
            "year": year_mfg,
            "id": c7_c10,
            "check_digit": c11
        }

    @staticmethod
    def validate_checksum(number_str):
        clean_num = ''.join(filter(str.isdigit, number_str))
        if len(clean_num) != 11:
            return False
        
        digits = [int(d) for d in clean_num[:10]]  # C1 to C10
        
        # Step 1: Sum even positions (C2,C4,C6,C8,C10) → 1-based indexing
        s1 = digits[1] + digits[3] + digits[5] + digits[7] + digits[9]
        
        # Step 2: Multiply by 3
        s2 = s1 * 3
        
        # Step 3: Sum odd positions (C1,C3,C5,C7,C9)
        s3 = digits[0] + digits[2] + digits[4] + digits[6] + digits[8]
        
        # Step 4: Add them
        s4 = s2 + s3
        
        # Step 5-6: Check digit = (10 - (s4 % 10)) % 10
        expected_check = (10 - (s4 % 10)) % 10
        actual_check = int(clean_num[10])
        
        return expected_check == actual_check