# Feature Development — Code Templates & Examples

> Loaded on-demand by `feature-development.md`. Do NOT read unless building a new feature.

---

## Entity Example

**Entity: `app/Customize/Entity/MyFeature.php`**
```php
<?php
namespace Customize\Entity;

use Doctrine\ORM\Mapping as ORM;

/**
 * @ORM\Table(name="dtb_my_feature")
 * @ORM\Entity(repositoryClass="Customize\Repository\MyFeatureRepository")
 * @ORM\HasLifecycleCallbacks()
 */
class MyFeature
{
    /**
     * @var int
     * @ORM\Column(name="id", type="integer", options={"unsigned":true})
     * @ORM\Id
     * @ORM\GeneratedValue(strategy="IDENTITY")
     */
    private $id;

    /**
     * @var string
     * @ORM\Column(name="name", type="string", length=255)
     */
    private $name;

    /**
     * @var string|null
     * @ORM\Column(name="description", type="text", nullable=true)
     */
    private $description;

    /**
     * @var bool
     * @ORM\Column(name="status", type="boolean", options={"default":true})
     */
    private $status = true;

    /**
     * @var \DateTime
     * @ORM\Column(name="create_date", type="datetimetz")
     */
    private $create_date;

    /**
     * @var \DateTime
     * @ORM\Column(name="update_date", type="datetimetz")
     */
    private $update_date;

    public function getId(): ?int { return $this->id; }
    public function getName(): ?string { return $this->name; }
    public function setName(string $name): self { $this->name = $name; return $this; }
    // ... other getters/setters

    /** @ORM\PrePersist */
    public function prePersist(): void
    {
        $this->create_date = new \DateTime();
        $this->update_date = new \DateTime();
    }

    /** @ORM\PreUpdate */
    public function preUpdate(): void
    {
        $this->update_date = new \DateTime();
    }
}
```

---

## Repository Example

**Repository: `app/Customize/Repository/MyFeatureRepository.php`**
```php
<?php
namespace Customize\Repository;

use Customize\Entity\MyFeature;
use Doctrine\Persistence\ManagerRegistry;
use Eccube\Repository\AbstractRepository;

class MyFeatureRepository extends AbstractRepository
{
    public function __construct(ManagerRegistry $registry)
    {
        parent::__construct($registry, MyFeature::class);
    }

    public function findActive(): array
    {
        return $this->createQueryBuilder('mf')
            ->where('mf.status = :status')
            ->setParameter('status', true)
            ->orderBy('mf.create_date', 'DESC')
            ->getQuery()
            ->getResult();
    }

    public function searchByName(string $keyword): array
    {
        return $this->createQueryBuilder('mf')
            ->where('mf.name LIKE :keyword')
            ->setParameter('keyword', '%' . $keyword . '%')
            ->getQuery()
            ->getResult();
    }
}
```

---

## Service Example

**Service: `app/Customize/Service/MyFeatureService.php`**
```php
<?php
namespace Customize\Service;

use Customize\Entity\MyFeature;
use Customize\Repository\MyFeatureRepository;
use Doctrine\ORM\EntityManagerInterface;

class MyFeatureService
{
    private EntityManagerInterface $entityManager;
    private MyFeatureRepository $repository;

    public function __construct(
        EntityManagerInterface $entityManager,
        MyFeatureRepository $repository
    ) {
        $this->entityManager = $entityManager;
        $this->repository = $repository;
    }

    public function create(MyFeature $feature): MyFeature
    {
        $this->entityManager->beginTransaction();
        try {
            $this->entityManager->persist($feature);
            $this->entityManager->flush();
            $this->entityManager->commit();
            return $feature;
        } catch (\Exception $e) {
            $this->entityManager->rollback();
            throw $e;
        }
    }

    public function update(MyFeature $feature): MyFeature
    {
        $this->entityManager->flush();
        return $feature;
    }

    public function delete(MyFeature $feature): void
    {
        $this->entityManager->remove($feature);
        $this->entityManager->flush();
    }

    public function getActiveFeatures(): array
    {
        return $this->repository->findActive();
    }
}
```

---

## Form Type Example

**Form: `app/Customize/Form/Type/MyFeatureType.php`**
```php
<?php
namespace Customize\Form\Type;

use Customize\Entity\MyFeature;
use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\Extension\Core\Type\CheckboxType;
use Symfony\Component\Form\Extension\Core\Type\TextareaType;
use Symfony\Component\Form\Extension\Core\Type\TextType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;
use Symfony\Component\Validator\Constraints as Assert;

class MyFeatureType extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('name', TextType::class, [
                'label' => 'Name',
                'constraints' => [
                    new Assert\NotBlank(),
                    new Assert\Length(['max' => 255]),
                ],
            ])
            ->add('description', TextareaType::class, [
                'label' => 'Description',
                'required' => false,
            ])
            ->add('status', CheckboxType::class, [
                'label' => 'Active',
                'required' => false,
            ]);
    }

    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults([
            'data_class' => MyFeature::class,
        ]);
    }
}
```

---

## Controller Example

**Controller: `app/Customize/Controller/MyFeatureController.php`**
```php
<?php
namespace Customize\Controller;

use Customize\Entity\MyFeature;
use Customize\Form\Type\MyFeatureType;
use Customize\Service\MyFeatureService;
use Eccube\Controller\AbstractController;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Template;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;

class MyFeatureController extends AbstractController
{
    private MyFeatureService $featureService;

    public function __construct(MyFeatureService $featureService)
    {
        $this->featureService = $featureService;
    }

    /**
     * @Route("/my_feature", name="my_feature_index")
     * @Template("MyFeature/index.twig")
     */
    public function index()
    {
        return ['features' => $this->featureService->getActiveFeatures()];
    }

    /**
     * @Route("/my_feature/create", name="my_feature_create")
     * @Template("MyFeature/edit.twig")
     */
    public function create(Request $request)
    {
        $feature = new MyFeature();
        $form = $this->createForm(MyFeatureType::class, $feature);
        $form->handleRequest($request);

        if ($form->isSubmitted() && $form->isValid()) {
            try {
                $this->featureService->create($feature);
                $this->addSuccess('Created successfully', 'admin');
                return $this->redirectToRoute('my_feature_index');
            } catch (\Exception $e) {
                $this->addError($e->getMessage(), 'admin');
            }
        }

        return ['form' => $form->createView(), 'feature' => $feature];
    }
}
```

---

## Routes Configuration

**Routes: `app/config/eccube/routes/my_feature.yaml`**
```yaml
my_feature_index:
    path: /my_feature
    controller: Customize\Controller\MyFeatureController::index
    methods: [GET]

my_feature_create:
    path: /my_feature/create
    controller: Customize\Controller\MyFeatureController::create
    methods: [GET, POST]

my_feature_edit:
    path: /my_feature/{id}/edit
    controller: Customize\Controller\MyFeatureController::edit
    methods: [GET, POST]
    requirements:
        id: \d+

my_feature_delete:
    path: /my_feature/{id}/delete
    controller: Customize\Controller\MyFeatureController::delete
    methods: [DELETE]
    requirements:
        id: \d+
```

---

## Service Registration

**Services: `app/config/eccube/services.yaml`**
```yaml
services:
    Customize\Repository\MyFeatureRepository:
        parent: 'Eccube\Repository\AbstractRepository'
        arguments:
            - '@doctrine'
        tags:
            - { name: 'doctrine.repository_service' }

    Customize\Service\MyFeatureService:
        arguments:
            - '@doctrine.orm.entity_manager'
            - '@Customize\Repository\MyFeatureRepository'
```

---

## SQL Schema Script

```sql
CREATE TABLE dtb_my_feature (
    id INT UNSIGNED AUTO_INCREMENT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description LONGTEXT DEFAULT NULL,
    status TINYINT(1) DEFAULT 1 NOT NULL,
    create_date DATETIME NOT NULL COMMENT '(DC2Type:datetimetz)',
    update_date DATETIME NOT NULL COMMENT '(DC2Type:datetimetz)',
    PRIMARY KEY(id)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ENGINE = InnoDB;

CREATE INDEX idx_status ON dtb_my_feature (status);
```
