from faker import Faker

fake = Faker()  # create an instance
print(fake.name())      # generates a random name
print(fake.address())   # generates a random address
print(fake.email())     # generates a random email
