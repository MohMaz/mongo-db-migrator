# Migration Report: Transition from JPA to MongoDB in Spring PetClinic

This report summarizes the comprehensive migration effort to move the Spring PetClinic application from a JPA/Hibernate relational model to a MongoDB document model. It covers the key steps—including code analysis, schema design decisions, implementation details, testing strategy, and migration planning—based on our group chat messages and tool outputs.

---

## 1. Code Analysis Results

The initial Analyzer agent scanned the cloned [Spring PetClinic codebase](cloned_repos/spring-petclinic/) and reported the following key observations:

- **Test Coverage:** The codebase includes numerous integration and unit tests, such as integration tests for owners, vets, embedded domain objects (pets, visits), and validators. Test classes like `OwnerRepositoryTests.java`, `VetRepositoryTests.java`, and `OwnerEntityIntegrationTests.java` verify CRUD operations.
- **Domain Model Structure:** The existing domain model uses JPA annotations on top of POJOs (e.g., `@Entity`, `@Table`, `@MappedSuperclass`). There are clearly separated entities for owners, vets, pets, visits, and even specialized lookup data (e.g., PetType).
- **Repository Interfaces:** Repository interfaces implement standard CRUD functionality for relational persistence and use method–based query derivation (e.g. `findByLastName` in the OwnerRepository).

These insights validate the necessity for a migration that accommodates embedding and document-level data management according to MongoDB’s capabilities.

---

## 2. Schema Design Decisions

Based on the discussions by the SchemaDesigner and SchemaValidator, the following design decisions have been made for the new MongoDB schema:

### 2.1. Document Structure

- **Owners Collection:**  
  - **Embedding:** Owners will embed their related pets along with each pet’s visits.  
  - **Indexing:** An index on `lastName` is recommended for faster lookup.

- **Vets Collection:**  
  - **Embedding:** Vet documents will embed a list of specialties.
  - **Indexing:** An index on `lastName` (and optionally specialty data) is advised.

- **PetTypes Collection (Optional):**  
  - **Lookup:** Although each pet embeds a snapshot of its PetType, a separate PetTypes collection is optional for maintaining consistent pet type definitions.

### 2.2. Data Modeling Rationale

- **Embedding vs. Referencing:**  
  - **Pets and Visits:** Embedding these within the Owner document enhances data locality since an owner typically has few pets and visits.
  - **Lookup Data (PetType):** Allowing for either an embedded snapshot or a separate collection increases flexibility—best for data that rarely changes.
  
- **Validation and Constraints:**  
  - MongoDB’s JSON-schema validation ensures that required fields (e.g., `firstName`, `lastName`, `telephone`) are enforced on the document level.
  - Dates will be stored as ISODate objects, and reference fields like ObjectId are validated accordingly.

### 2.3. Example MongoDB Collection Schemas

Below are one-line sample `createCollection` commands for schema validation:

- **Owners Collection:**

  ```javascript
  db.createCollection("owners", {validator: {$jsonSchema: {"bsonType": "object", "required": ["firstName","lastName","address","city","telephone","pets"], "properties": {"firstName": {"bsonType": "string", "description": "Owner firstName must be a string and is required"}, "lastName": {"bsonType": "string", "description": "Owner lastName must be a string and is required"}, "address": {"bsonType": "string", "description": "Owner address must be a string and is required"}, "city": {"bsonType": "string", "description": "Owner city must be a string and is required"}, "telephone": {"bsonType": "string", "description": "Owner telephone must be a string and is required"}, "pets": {"bsonType": "array", "items": {"bsonType": "object", "required": ["name","birthDate","type","visits"], "properties": {"name": {"bsonType": "string", "description": "Pet name must be a string and is required"}, "birthDate": {"bsonType": "date", "description": "Pet birthDate must be a date and is required"}, "type": {"bsonType": "object", "required": ["name"], "properties": {"_id": {"bsonType": "objectId", "description": "Optional pet type reference"}, "name": {"bsonType": "string", "description": "Pet type name must be a string and is required"}}}, "visits": {"bsonType": "array", "items": {"bsonType": "object", "required": ["date","description"], "properties": {"date": {"bsonType": "date", "description": "Visit date must be a date and is required"}, "description": {"bsonType": "string", "description": "Visit description must be a string and is required"}}}}}}}}}, "validationLevel": "strict", "validationAction": "error"})
  ```

- **Vets Collection:**

  ```javascript
  db.createCollection("vets", {validator: {$jsonSchema: {"bsonType": "object", "required": ["firstName","lastName","specialties"], "properties": {"firstName": {"bsonType": "string", "description": "Vet firstName must be a string and is required"}, "lastName": {"bsonType": "string", "description": "Vet lastName must be a string and is required"}, "specialties": {"bsonType": "array", "items": {"bsonType": "object", "required": ["name"], "properties": {"_id": {"bsonType": "objectId", "description": "Optional specialty id"}, "name": {"bsonType": "string", "description": "Specialty name must be a string and is required"}}}}}}}, "validationLevel": "strict", "validationAction": "error"})
  ```

- **PetTypes Collection (Optional):**

  ```javascript
  db.createCollection("pettypes", {validator: {$jsonSchema: {"bsonType": "object", "required": ["name"], "properties": {"name": {"bsonType": "string", "description": "PetType name must be a string and is required"}}}}, "validationLevel": "strict", "validationAction": "error"})
  ```

---

## 3. Implementation Details

### 3.1. Domain Model Updates

The new implementation replaces JPA annotations with Spring Data MongoDB annotations. An example of updated domain classes is provided below:

#### Owner.java
```java
package org.springframework.samples.petclinic.model;

import java.util.List;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;
import lombok.Data;

/**
 * Represents an owner document stored in the "owners" MongoDB collection.
 * An owner has personal details and an embedded list of pets.
 */
@Data
@Document(collection = "owners")
public class Owner {

    @Id
    private String id;
    private String firstName;

    @Indexed
    private String lastName;
    private String address;
    private String city;
    private String telephone;
    private List<Pet> pets;
}
```

#### Pet.java
```java
package org.springframework.samples.petclinic.model;

import java.util.Date;
import java.util.List;
import lombok.Data;

/**
 * Represents a pet owned by an Owner.
 * Each pet contains a name, a birth date, an embedded snapshot of PetType, and a list of visits.
 */
@Data
public class Pet {
    private String id; // Optional for embedded objects
    private String name;
    private Date birthDate;
    private PetType type;
    private List<Visit> visits;
}
```

#### Other Domain Classes

- **Visit.java:** Represents pet visit records.
- **Vet.java:** Uses `@Document(collection = "vets")` and embeds a list of specialties.
- **Specialty.java & PetType.java:** Updated similarly with removal of JPA annotations.

### 3.2. Repository Interface Changes

Repository interfaces are updated to extend `MongoRepository` instead of JPA repositories. For example:

```java
package org.springframework.samples.petclinic.repository;

import java.util.List;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.samples.petclinic.model.Owner;

/**
 * Repository interface for Owner documents.
 */
public interface OwnerRepository extends MongoRepository<Owner, String> {
    List<Owner> findByLastName(String lastName);
}
```

Similarly, the `VetRepository` is updated accordingly.

---

## 4. Testing Approach

The testing strategy has been revised to validate the new MongoDB persistence layer while leveraging Testcontainers for an ephemeral MongoDB instance.

### 4.1. Repository Tests

Using Spring Boot’s `@DataMongoTest` annotation, repository tests ensure that documents with embedded objects are correctly persisted and retrieved.

#### Example: OwnerRepositoryTests.java
```java
package org.springframework.samples.petclinic.repository;

import static org.assertj.core.api.Assertions.assertThat;
import java.util.Arrays;
import java.util.Date;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.data.mongo.DataMongoTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.samples.petclinic.model.Owner;
import org.springframework.samples.petclinic.model.Pet;
import org.springframework.samples.petclinic.model.Visit;
import org.springframework.samples.petclinic.model.PetType;
import org.testcontainers.containers.MongoDBContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataMongoTest
@Testcontainers
public class OwnerRepositoryTests {

    @Container
    static MongoDBContainer mongoDBContainer = new MongoDBContainer("mongo:5.0.5");

    @DynamicPropertySource
    static void setProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.data.mongodb.uri", mongoDBContainer::getReplicaSetUrl);
    }

    @Autowired
    private OwnerRepository ownerRepository;

    @Test
    public void testSaveOwnerWithEmbeddedPetsAndVisits() {
        // Create a snapshot for pet type
        PetType petType = new PetType();
        petType.setName("Dog");

        // Create a visit record
        Visit visit = new Visit();
        visit.setDate(new Date());
        visit.setDescription("Annual checkup");

        // Create a pet with embedded values
        Pet pet = new Pet();
        pet.setName("Buddy");
        pet.setBirthDate(new Date());
        pet.setType(petType);
        pet.setVisits(Arrays.asList(visit));

        // Create an owner embedding the pet
        Owner owner = new Owner();
        owner.setFirstName("John");
        owner.setLastName("Doe");
        owner.setAddress("123 Main St");
        owner.setCity("Anytown");
        owner.setTelephone("555-1234");
        owner.setPets(Arrays.asList(pet));

        Owner savedOwner = ownerRepository.save(owner);
        Owner found = ownerRepository.findById(savedOwner.getId()).orElse(null);

        assertThat(found).isNotNull();
        assertThat(found.getLastName()).isEqualTo("Doe");
        assertThat(found.getPets()).hasSize(1);
        Pet foundPet = found.getPets().get(0);
        assertThat(foundPet.getName()).isEqualTo("Buddy");
        assertThat(foundPet.getVisits()).hasSize(1);
        assertThat(foundPet.getType().getName()).isEqualTo("Dog");
    }
}
```

### 4.2. Integration Testing

Full integration tests using `@SpringBootTest` load the complete Spring context and verify end-to-end interaction with the MongoDB instance (configured via Testcontainers).

---

## 5. Migration Plan Summary

The high-level migration plan follows these steps:

1. **Update Dependencies & Configuration:**  
   – Remove JPA/Hibernate and JDBC dependencies; add Spring Data MongoDB.  
   – Update `application.properties` to configure `spring.data.mongodb.uri`.

2. **Modify Domain Entities:**  
   – Replace JPA annotations (`@Entity`, `@Table`) with MongoDB-specific annotations (`@Document`).  
   – Update identifier fields (typically use String or ObjectId).  
   – Remove unnecessary JPA annotations from embedded domain objects.

3. **Migrate Repository Interfaces:**  
   – Change repository interfaces to extend `MongoRepository` and adjust query methods as needed.

4. **Adjust Database Configuration:**  
   – Remove JDBC settings entirely and use the MongoDB connection URI.  
   – Leverage Testcontainers for dynamic environment configuration during testing.

5. **Update the Service Layer:**  
   – Autowire and interact with the MongoRepository-based interfaces.  
   – Remove or rectify transactional annotations as required.

6. **Revise Testing Infrastructure:**  
   – Update unit tests to use `@DataMongoTest` and integration tests to use `@SpringBootTest`.  
   – Utilize Testcontainers to spin up a temporary MongoDB instance for consistent test environments.

7. **Data Migration Strategy (if needed):**  
   – Export legacy relational data (e.g., as JSON).  
   – Develop ETL scripts to transform the data into MongoDB’s document structure (embed pets and visits appropriately).  
   – Test the migration process in staging prior to production rollout.

8. **Documentation and Code Cleanup:**  
   – Update all documentation and Javadoc to reflect MongoDB’s data model.  
   – Remove outdated JPA code, configurations, and dependencies.

---

## 6. Conclusion

This migration re-architects the Spring PetClinic application to leverage MongoDB’s document-oriented data model. By embedding related data (pets, visits, and specialties) within top-level documents and using appropriate schema validation and indexing strategies, the application is now poised to benefit from improved performance and data locality. The updated codebase, configuration adjustments, and robust testing infrastructure ensure both a smooth migration and long-term maintainability.

This report, along with the provided code samples and detailed migration plan, serves as a roadmap to successfully complete the transition from JPA to MongoDB.