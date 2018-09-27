## Synopsis

Chose area from OpenStreetMap data and used data mining techniques, such as accessing the quality of the data for validity, accuracy, completeness, consistency, and uniformity, to clean the OpenStreetMap data for the area chosen. After, used SQL as the data schema to complete project.

## Code Example

```python
 
    #Step 1. Identify the street type using regex pattern matching
    #Step 2. Find the "better" street type using user defined "matching" dictionary
    #Step 3. Replace old street_type with better street_type

    #Step 1
    print('name: {}'.format(name)) # Print original street name
    m = street_type_re.search(name) # Search name for regex pattern for street type
    
    if m: # Check if the refex pattern for street type was found
        street_type = m.group()
        print('m.group() output: {}'.format(street_type)) # Print street type
    
    #Step 2    
    better_type = street_type # Initialized the "better" street type variable    
    for problem_type in mapping:
        if street_type == problem_type:
            better_type = mapping[problem_type]
            
    #Step 3
    better_name = name.replace(street_type, better_type) #replace the street type with better_type
    print('better_name: {}'.format(better_name)) #print better street name
    
    return better_name
```
